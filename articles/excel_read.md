---
title: Scala + shapelessでExcelパーザーを自動生成
tags: Scala 関数型プログラミング Excel macro
author: yyu
slide: false
---
# はじめに

最近は業務でScalaを使ってExcelを解析するプログラムを保守・運用している。Excelは、JSONやXML、YAMLといった他のデータフォーマットと異なり、非エンジニアであっても編集することができるというのが大きな特徴であるが、その代償として限定されたデータ構造しか記述できない。
Scalaにおいては、たとえばJSONは[Play JSON](https://github.com/playframework/play-json)のようにScalaのケースクラスからマクロを用いてパーザーを自動生成するというのが普及している。一方でExcelにはそのようなものが（筆者らが知る限りにおいて）存在しなかったため、これまでは[Poi Scala](https://github.com/folone/poi.scala)というパーザーを利用して、たとえば「あるシートの`1:A`を`Double`値として取得する」といった低レベルなプログラムを書く必要があった。そこで@ippei-takahashiがPlay JSONのようにマクロ（[shapeless](https://github.com/milessabin/shapeless)）を利用してExcelの行を表すケースクラスからパーザーを自動生成してパーズするライブラリーを開発した。また筆者はそのライブラリーをその部分だけで利用できるように簡単に修正し、またこの記事を執筆することにした。
この記事ではまずExcelのデータ構造について他のJSONなどと比較しつつ説明し、それがこのライブラリーでどのようにパーズできるかの例を示す。その後ライブラリーの実装について要所を解説し、最後にまとめを述べる。
この記事で説明するライブラリーの全ソースは下記のGitHubリポジトリーから参照できる。

- https://github.com/y-yu/excel-reads

この記事を読んで疑問点や改善点がある場合は、気軽にコメントなどで教えてほしい。

# Excel _vs_ JSON

ほとんどの人はExcelを1度は使ったことがあると思うが、Excelは次のように**シート**と呼ばれる行列にデータを入れていくことができるシステムである。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/0a06552f-0511-41bb-a94e-fc522f98827b.png" width="60%"/>

上記の図では`sheet1`というシートにデータを書き込んでいる。シートの名前は重複しない限り任意の文字列で与えられ、たとえば別のシートである`sheet2`は次のようになっている。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/2fa9f50c-ae12-cd23-8cfb-e827f5a8c96d.png" width="60%"/>

このようなシンプルな構造なのでExcelで表現できる全てのデータはJSONで模倣できる[^cell-type]。たとえば上記の画像のExcelはJSONで次のように模倣できる。

```json
{
  "sheet1": [
    [0, 1, 2, "hello", "world"],
    [true, 3.14]
  ],
  "sheet2": [
    ["this", "is", "a", "pen"]
  ]
}
```

[^cell-type]: 厳密に言えばExcelにはJSONには存在しない日付型や数式型などを持っているが、ここで重要な点はExcelのセルの型というよりは、オブジェクトの中にオブジェクトをネストできないといった構造の制約であるため、この差はひとまず無視するここにする。

このJSONのようなものがExcelのデータ構造である。重要な点を次にまとめる。

- JSONはオブジェクト（連想配列）を任意にネストすることができるが、Excelではオブジェクトをトップレベルでしか利用できない
- JSONはオブジェクトの値に任意のJSONを利用できるが、Excelは二次元配列しか利用できない
    - したがって、Excelの配列の要素は任意のプリミティブな値（数値、文字列、真偽値など）を入れることができるが、オブジェクトや配列を入れてはならない

このようなExcelデータを簡単にパーズすることを目指す。

# Excel Reads

ここでは作成したライブラリーであるExcel Readsの使い方と実装について説明する。

## 使い方

まずはExcelの行に対応するケースクラスを用意する。

```scala
case class HelloWorld(
  hello: String,
  world: String
)
```

そして次のExcelを与える。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/1410fa74-17d3-35a5-8837-7c7e36cff125.png" width="50%"/>

このファイルをPoi Scalaで読み込むと次のような抽象データ構造へと変換される。

```scala
val rowWithSheetName = RowWithSheetName(
  "sheet",
  Row(1) {
    Set(StringCell(1, "hello"), StringCell(2, "world"))
  }
)
```

`RowWithSheetName`はライブラリーが提供するデータ構造で、行とシート名の組である。あとは先程の`HelloWorld`を型パラメーターとしてパーザーを起動するだけである。

```scala
ExcelReads[HelloWorld].read(rowWithSheetName) // Success(HelloWorld("hello", "world"))
```

パーザーの結果は[Scalaz](https://github.com/scalaz/scalaz)の`ValidationNel`[^validation-nel]であり、`Success`は成功を表す。

[^validation-nel]: `Validation[A, B]`の`A`を`NonEmptyList`に強制したものであり次のように定義される。

    ```scala
    type ValidationNel[A, B] = Validation[NonEmptyList[A], B]
    ```

## 実装の説明

まずは型クラス`ExcelReads`によってパーザーが定義・自動生成される。

```scala:ExcelReads.scala
trait ExcelReads[A] {
  protected def parseState(
    rowWithSheetName: RowWithSheetName
  ): State[Int, ValidationNel[ExcelRowParseError, A]]

  def read(
    rowWithSheetName: RowWithSheetName,
    initial: Int = 1
  ): ValidationNel[ExcelRowParseError, A] =
    parseState(rowWithSheetName).eval(initial)

  def map[B](f: A => B): ExcelReads[B] = { rowWithSheetName =>
    parseState(rowWithSheetName).map(_.map(f))
  }
}
```

まず型パラメーター`A`はパーズの結果得られる結果の型である。パーズ結果は関数`read`の結果の型`ValidationNel[ExcelRowParseError, A]`を返す。`String`や`Int`などについては自明な型としてあらかじめデフォルトのインスタンスが与えられている。

```scala:ExcelReads.scala
implicit val parserStringOption: ExcelReads[Option[String]] = { rowWithSheetName =>
  State { s =>
    (
      s + 1,
      rowWithSheetName.row.cells.find(_.index == s).map {
        case StringCell(_, data) =>
          Success(data.trim)
        case cell =>
          failureNel(
            UnexpectedTypeCell(
              errorIndex = s,
              expectedCellType = StringCellType,
              actualCellType = CellType.fromCell(cell)
            )
          )
      }.sequence
    )
  }
}
```

まずは上記のように`Option[String]`のような`Option[?]`の型のインスタンスを作成する。`State[Int, ?]`の`Int`は列方向のインデックスを示している。たとえば`s + 1`という処理は、1つセルをパーズしたので次のセルへと移動するという処理である。このようにStateモナドを利用しているため、たとえば3つのセルを利用するといったパーザーも自由に書くことができる。
そして`Option[A]`のインスタンスから`A`のインスタンスを次のように導出する。

```scala:ExcelReads.scala
implicit def parseA[A](implicit R: ExcelReads[Option[A]]): ExcelReads[A] = { rowWithSheetName =>
  for {
    validation <- R.parseState(rowWithSheetName)
    s <- State.get[Int]
  } yield validation andThen {
    case Some(a) => Success(a)
    case None => failureNel(UnexpectedEmptyCell(s - 1))
  }
}
```

このようにするため、たとえば`Option[Option[A]]`のような`Option`がネストした型をパーズすることはできない。しかし、ネストした`Option`型の値に対応するExcel表現が自明ではないことから、コードのシンプルさを優先してこのようなインスタンスとした。
また、`Seq[A]`は`A`のインスタンスを利用して次のようになる。

```scala:ExcelReads.scala
implicit def parserSeq[A](implicit R: ExcelReads[A]): ExcelReads[Seq[A]] = { rowWithSheetName =>
  val row = rowWithSheetName.row

  State { s =>
    val res: Seq[ValidationNel[ExcelRowParseError, A]] = unfold(s) { x =>
      val (next, value) = R.parseState(rowWithSheetName)(x)

      value match {
        case v @ Success(_) =>
          Some((v, next))
        case v @ Failure(_) =>
          if (row.cells.exists(_.index >= x))
            // Even if an error occurred at somewhere in the row,
            // it parses at the end to concat all errors.
            Some((v, next))
          else
            // Otherwise parsing is done.
            None
      }
    }

    (
      s + res.length,
      res.foldRight[ValidationNel[ExcelRowParseError, Seq[A]]](Success(Nil)) {
        (xv, acc) =>
          xv.ap(acc.map(xs => x => x +: xs))
      }
    )
  }
}
```

やや大きいコードだが、次のような特徴がある。

- `Validation`型を利用している利点を活かすため、たとえパーズに失敗したとしても空のセルが出現するまでパーズを続けて可能な限りエラーを集めるようにしている
- 簡単のためこの実装はバックトラックのような仕組みを搭載していない。したがってこのコードはケースクラスの末尾に`Seq`がある場合にのみしか正常に動作しない
    - 正規表現エンジンのようにバックトラックを実装することで、`Seq`がケースクラスのどの位置においても使えるようにするという戦略もあるが、しかしそうすると正規表現のように`*`が貪欲かそうでないか、などといった複雑さも生じる
    - これらの複雑さとユースケースを勘案した結果、ひとまずは末尾でのみ`Seq`が使えれば十分であろうと考えてこの実装を与えた

最後に`HList`に関するインスタンスを作成する。`HList`はshapelessの機能でケースクラスからマクロで`HList`へ変換するため必要になる。

```scala:ExcelReads.scala
implicit val parserHNil: ExcelReads[HNil] = { _ =>
  State(s => (s, Success(HNil: HNil)))
}

implicit def parserHCons[H, T <: HList](
  implicit head: ExcelReads[H],
  tail: ExcelReads[T]
): ExcelReads[H :: T] = { rowWithSheetName =>
  for {
    hv <- head.parseState(rowWithSheetName)
    tv <- tail.parseState(rowWithSheetName)
  } yield
    hv.ap(tv.map(t => h => h :: t))
}

implicit def parserHList[A, L <: HList](
  implicit gen: Generic.Aux[A, L],
  parserHList: Lazy[ExcelReads[L]]
): ExcelReads[A] = { rowWithSheetName =>
  parserHList.value.parseState(rowWithSheetName).map(_.map(gen.from))
}
```

このようになっているが、特別に説明するところはないと思う。注意するべきなのは`Coproduct`のインスタンスは用意されていないということである。たとえば次のようなケースクラス`User`をデフォルトのインスタンスでパーズすることはできない。

```scala
sealed trait Sex
case class Male(value: String) extends Sex
case class Female(value: String) extends Sex

case class User(
  name: String,
  age: Int,
  sex: Sex
)

val rowWithSheetName = ???

ExcelReads[User].read(rowWithSheetName) // compile error!
```

これに対応するExcelは次のようになる。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/20d25900-2601-7788-fd47-d3bf8a2ab849.png" width="50%"/>

代数的データ型（ADT）であるような「このうちのどれか」という構造のパーズを汎用に行なうためには`Coproduct`のインスタンスが必要になる。しかし次のような理由でデフォルトのインスタンスでこれは用意していない。

- shapelessによるケースクラスから`HList`への変換は、引数（フィールド）の並びと`HList`上の型の並びが対応するため順序が明らかに自明であるが、一方で代数的データ型の場合はどのような順序の`Coproduct`が生成されるのかshapelessの実装次第となると思われる
- そのため、たとえば`Either[Double, Int]`のようなとき、Excelのセルでは`Double`と`Int`に区別がないため、どちらでパーズするのかに何らかの優先順位が必要になる
    - 上記の`User`の例では`String`と`String`であるため、型だけで区別することは不可能である
- たとえば正規表現では`A | B`のように書いた場合、正規表現`A`にも`B`にもマッチする場合は左を優先して`A`にマッチしたとする、といったルールがある
    - このようなルールは（正規表現エンジンごとに違いが多少あるとはいえ）正規表現の文字列としての表現からある程度知ることができるが、`Coproduct`の生成方法はshapeless任せなのでこの実装を知っていなければならない
    - 型レベルリスト（`HList`）などで優先順位を与えるという方法もあるが、議論として`Either`のようなものが必要な場合は、一旦どちらも可能な1つのデータ型として解釈しておき、そのあとドメインモデルなどへバリデーション処理をしつつ変換するときにより厳密にすればよいという結論となった
    - Excelの解釈によって生まれるデータ型は、あくまでもData Transfer Object（DTO）であろうから、あまり複雑なバリデーションや変換をこのフェーズで一気にやる必要はないと判断した
- このような検討の末、ひとまずのところは`Coproduct`のインスタンスは作成しなかった

このようにして`ExcelReads`のインスタンスが定義されている。

# まとめ

このようExcelからケースクラスへのパーザーをshapelessで自動生成するようなものを作成した。今後の課題として、本文でも説明したが`Seq`をケースクラスの途中でも使えた方がなにかと便利そうな気はする。そのため多少は複雑になるが、このシステムがもし使えそうとなった時には、正規表現のようなバックトラックを導入したり、正規表現に近いDSLを導入して貪欲かどうかなどを与えられるようにしたい。

# 議論 （余談）

この実装が生まれたときの議論を紹介しておく。Excelのデータ構造がJSONで模倣できるので、JSONからケースクラスへ変換するPlay JSONがある以上この変換は可能であると思われていたが、使いやすいものになるかどうかという点が謎であった。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/53a67b1e-b805-c993-9fdf-db3a70fa3262.png" width="70%">

とはいえ作って使ってみないと分からないということで（？）@ippei-takahashiにより実装が行なわれた。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/88b172b0-dae5-dd57-9efe-a7ba9da5e3c4.png" width="70%"/>

まだこのライブラリーを利用してがっつりとプログラムを書いたわけではないので、今後使ってみてどんどん洗練させていきたい。

## 追記

`Seq`を任意の場所に置くためにバックトラックについて考えていたところ、[ねこはる君がScalaMatsuri2019で発表](https://www.slideshare.net/SanshiroYoshida/making-logic-monad)していたMonadPlusを使ったテクニックを利用すればいいのでは？と思い彼に相談してみたところ👇というふうになった……。

- <blockquote class="twitter-tweet" data-conversation="none"><p lang="ja" dir="ltr">List[State[Int, ValidationNel[Error, A]]]👈こういう感じでMonadPlusにしてバックトラックを搭載したらどうですかね？とねこはる君に相談したけど、複雑になりすぎて使えなくなりますよーという感じになった……😇</p>&mdash; 吉村 優 / YOSHIMURA Yuu (@_yyu_) <a href="https://twitter.com/_yyu_/status/1171006387997962245?ref_src=twsrc%5Etfw">September 9, 2019</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    - ようするに、たとえば次のようなケースクラスを考える
    
        ```scala
        case class TwoStringSeq(
          seq1: Seq[String],
          seq2: Seq[String]
        )
        ```
    - このようにしたとき、正規表現では`(\w*)(\w*)`のようなものになると言えるので、`seq1`に貪欲にマッチして`seq2`は空となるという1つの戦略がある。しかし、正規表現では慣用的にこのように振る舞うが、こうでなければならないというわけでもない
    - したがってExcel上の表記と型との間の関係がどんどんと非自明になってしまう
    - このような議論があって`Coproduct`のインスタンスをあえて作らなかったので、このような途中にあらわれる`Seq`もなくてよいのではないか
    - 一方で`HList`のインスタンスを改良することで、ケースクラスの末尾以外に`Seq`がある場合はコンパイルエラーとすることができそう
        - こちらはやる価値があるのではないか
- <blockquote class="twitter-tweet" data-conversation="none"><p lang="ja" dir="ltr">何ひとつ 主張できない 予感して（575） <a href="https://t.co/ONWDHORVzA">pic.twitter.com/ONWDHORVzA</a></p>&mdash; 吉村 優 / YOSHIMURA Yuu (@_yyu_) <a href="https://twitter.com/_yyu_/status/1171066816870809600?ref_src=twsrc%5Etfw">September 9, 2019</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    - `Validation`はアプリカティブなので、エラーを同時にいくつも集めることができるがバックトラックした場合、どのエラーを表示するのがよいのか分からなくなる
    - バックトラックした組み合せを全てエラー表示すると、ユーザーにとって使いやすいものではなくなりそう
    - したがってバックトラックを入れてしまうと`Validation`をつかっている意味が薄れるのではないか？

このあとで`List[State[Int, ValidationNel[Error, A]]`は`StateT`をつかって`StateT[List, ValidationNel[Error, A]]`の方がいいですね、という話をした。

