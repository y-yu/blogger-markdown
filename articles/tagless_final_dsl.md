[前回の記事](http://qiita.com/yyu/items/a2debfcde8f1915d5083)では、ReaderモナドやFreeモナドを使ってDependency Injectionを行うための小さなDSLを組み立てた。今回の記事では、まず前回組み立てたDSLの課題である**Expression Problem**と、それを解決するための機能**Inject**と、さらには**Tagless Final**を用いたDSLについて述べる。
この記事は前回の記事の知識を前提としているので、分からない言葉などがある場合はまず前回の記事を参照して欲しい。また、文章について不明なことや意図が分かりにくい部分があれば気軽に指摘して欲しい。

> 注意：
> 記事の中にあるコードは読みやすさのために`import`などを省略しているので、このままでは動かない。動かしたい方は[Githubのリポジトリ](https://github.com/yoshimuraYuu/DIwithTaglessFinal)を使うとよい。

# Expression Problem
Expression Problemとは、[こちらのサイト](http://maoe.hatenadiary.jp/entry/20101214/1292337923)を引用すると次のようになる。

> 1. 静的型を使っていて
> 2. 再コンパイルすることなく
> 3. データ型や
> 4. 操作を増やすのが難しい

ということになる。具体的な例を挙げると、まず今のTwitter操作DSLにツイートを削除する機能を追加しようとしたとする。まず次のようにデータ型を用意する。

```scala
sealed trait Twitter[A]

case class Fetch[A](screenName: String, next: WSResponse => A) extends Twitter[A]
case class Update[A](status: String, next: A) extends Twitter[A]
case class Delete[A](id: String, next: A) extends Twitter[A]
```

この時点では、先ほど既に書いたインタープリターとDSLは`Delete`が存在しない時代に書かれたものなので、インタープリターは`Delete`についてカバーしていなくてもよいことは自明であるが、Scalaのコンパイラにはそれが分からないので次のような警告が出る。

```
Warning:(14, 47) match may not be exhaustive.
It would fail on the following input: Delete(_, _)
    def map[A, B](a: Twitter[A])(f: A => B) = a match {
                                              ^
```

警告を無視するというのも一つの手だが、ようするにこのアプローチでは一つの代数的データ型を参照するので、その代数的データ型を拡張するとそれを使っている既存のありとあらゆる関数が影響を受けてしまう。
そこで、InjectまたはTagless Finalを用いてこれを回避する。

# InjectとCoproduct

Inject（Coproduct）の考え方は、今ある代数的データ型`Twitter`に`Delete`を追加せずに、新たに次のような代数的データ型を作って対応するというものである。

```scala:DeleteOfTwitter.scala
sealed trait DeleteOfTwitter[A]

case class Delete[A](id: String, next: A) extends DeleteOfTwitter[A]
```

さて、これで`Twitter`を拡張してはいないのでExpression Problemは発生しないが、この`Twitter`と`DeleteOfTwitter`は関係のない型になってしまったので、一つの型としてまとめて取り扱うことができない。そこで、二つの型を取り扱えるようなデータ構造として**Coproduct**を導入する。

## Coproduct

`Coproduct`は次のように定義される。

```scala:Coproduct.scala
case class Coproduct[F[_], G[_], A](value: Either[F[A], G[A]])
```

このように、`value`として`Either`の値を持つだけであるが、これだけで実はもう、`Twitter`と`DeleteOfTwitter`を混ぜ合わせることができる。
まず、これからの説明を簡単にするために次の型`TwitterWithDelete`を作っておく。

```scala
type TwitterWithDelete[A] = Coproduct[Twitter, DeleteOfTwitter, A]
```

さて、`Twitter`と`DeleteOfTwitter`を`Coproduct`を用いて混ぜるためには、Freeモナドの定義を思いだす必要がある。Freeモナドは次のような定義になっている。

```scala:Free.scala
case class Done[F[_]: Functor, A](a: A) extends Free[F, A]
case class More[F[_]: Functor, A](k: F[Free[F, A]]) extends Free[F, A]
```

注目するべきは`More`の引数`k`である。`k`の型は`F[Free[F, A]]`となっており、今までの例ではこの`F`に`Twitter`を入れて用いていた。では`Twitter`のかわりに`TwitterWithDelete`を入れて、つまり`Free[TwitterWithDelete, A]`とするとどうなるだろうか。そのためにはまず、`TwitterWithDelete`の正体である`Coproduct`をファンクターにしなければならない。

```scala:Coproduct.scala
object Coproduct {
  implicit def coproductFunctor[F[_], G[_]](implicit F: Functor[F], G: Functor[G]) =
    new Functor[({type L[A] = Coproduct[F, G, A]})#L] {
      def map[A, B](a: Coproduct[F, G, A])(f: A => B): Coproduct[F, G, B] = a.value match {
        case Left(e)  => Coproduct[F, G, B](Left(F.map(e)(f)))
        case Right(e) => Coproduct[F, G, B](Right(G.map(e)(f)))
      }
    }
}
```

一見するとややこしいが、`Coproduct`の中身は単なる`Either`なので、`Either`の`map`とほとんど同じになる。
これで`Free[TwitterWithDelete, A]`が作れるようになったので、もう一度`Free`における`More`の定義を見直すことにする。

```scala
case class More[F[_]: Functor, A](k: F[Free[F, A]]) extends Free[F, A]
```

`F`には`TwitterWithDelete`が入るので、`More`の引数`k`の型は`TwitterWithDelete[Free[TwitterWithDelete, A]]`となる。`TwitterWithDelete`の型パラメーターは何に用いられているのかというと、この型パラメーターはそれぞれ`Twitter`と`DeleteOfTwitter`の型パラメーターとなっている。ではこれらの定義を見てみよう。

```scala:Twitter.scala
case class Fetch[A](screenName: String, next: WSResponse => A) extends Twitter[A]
case class Update[A](status: String, next: A) extends Twitter[A]
```

```scala:DeleteOfTwitter.scala
case class Delete[A](id: String, next: A) extends DeleteOfTwitter[A]
```

つまり、`TwitterWithDelete`の型パラメーター`Free[TwitterWithDelete, A]`は`next`の型として渡されていることになる。つまり、`next`は次のような能力を持つことになる。

<dl>
  <dt>次の処理がある（<code>More</code>）か無い（<code>Done</code>）か<dt>
  <dd>→ Freeモナドによる能力</dd>
  <dt>次の処理がある場合、それが右（<code>Twitter</code>）か左（<code>DeleteOfTwitter</code>）か</dt>
  <dd>→ Coproductによる能力</dd>
</dl>

このように、Coproductで`Either[Twitter, DeleteOfTwitter]`の値を持つようにしたため、“どちらか”という能力が強化された。
これを使って次のように二つを併せたDSLを書くことができる[^why_many]。

```scala:TwitterWithDelete.scala
object TwitterWithDelete {
  type TwitterWithDelete[A] = Coproduct[Twitter, DeleteOfTwitter, A]

  def left[A](l: Twitter[A]): Either[Twitter[A], DeleteOfTwitter[A]] = Left(l)
  def right[A](r: Delete[A]): Either[Twitter[A], DeleteOfTwitter[A]] = Right(r)
  def coproduct[A](a: Either[Twitter[A], DeleteOfTwitter[A]]) = Coproduct[Twitter, DeleteOfTwitter, A](a)
  def more[A](k: TwitterWithDelete[Free[TwitterWithDelete, A]]): Free[TwitterWithDelete, A] = More[TwitterWithDelete, A](k)
  def done[A](a: A): Free[TwitterWithDelete, A] = Done[TwitterWithDelete, A](a)

  val example: Free[TwitterWithDelete, Unit] =
    more(coproduct(left(Update("new tweet", more(coproduct(right(Delete("<id>", done()))))))))
}
```

[^why_many]: `left`や`right`などといった大量の補助関数は、Scalaの型推論を補助するために定義されている。

できあがったDSLは次の部分である。

```scala
more(coproduct(left(Update("new tweet", more(coproduct(right(Delete("<id>", done()))))))))
```

しかし、これは`more(coproduct(right(???)))`のような部分が繰り返しあり、どう見ても使い勝手が悪い。なので**Inject**を使ってこのDSLを改良する。

## Inject

Injectとは次のような関数を提供する[型クラス](http://halcat0x15a.github.io/slide/functional_scala/#/)である。

```scala:Inject.scala
sealed trait Inject[F[_], G[_]] {
  def inj[A](sub: F[A]): G[A]
}
```

この`Inject`は`F[A]`から`G[A]`へ変換する関数（メソッド）`inj`を提供する。`F`と`G`がなんでもよいとすれば、例えば`List[Int]`から`Option[Int]`へ変換できるということになるが、もちろんそんなことはなく、`inj`を定義するためには次のいずれかの条件を満す必要がある。

1. `Inject[F, F]`
2. `Inject[F, Coproduct[F, G, ?]]`[^type_lambda1]
3. `Inject[F, G]`を仮定して、`Inject[F, Coproduct[H, G, ?]]`[^type_lambda2]

これらのパターンについて、どうして関数`inj`が定義できるのかを考える。
まず、最初のケースは元の型と行き先の型が同じ`F`なので、受け取ったものをそのまま返せばよい。
次のパターンは、`F`は`G`について何も知らなかったとしても、`Coproduct[F, G, ?]`の左側は`F`であるのでこちらへ行くことができる。
最後のパターンは、まず`Inject[F, G]`を仮定するということについて考える。これを仮定するということは`F[A]`を引数に取り`G[A]`を返す関数`inj`が存在するということになる。この`inj`を用いてまず`F[A]`を`G[A]`へ変換すれば、`Coproduct[H, G, ?]`の右側となるので、こちらへ行くことができる。
これをScalaのコードへ翻訳すると次のようになる。

```scala:Inject.scala
object Inject {
  implicit def reflexive[F[_]:  Functor] = new Inject[F, F] {
    def inj[A](a: F[A]): F[A] = a
  }

  implicit def left[F[_]: Functor, G[_]: Functor] =
    new Inject[F, ({type L[A] = Coproduct[F, G, A]})#L] {
      def inj[A](a: F[A]): Coproduct[F, G, A] = Coproduct[F, G, A](Left(a))
    }

  implicit def right[F[_]: Functor, G[_]: Functor, H[_]: Functor](implicit I: Inject[F, G]) =
    new Inject[F, ({type L[A] = Coproduct[H, G, A]})#L] {
      def inj[A](a: F[A]): Coproduct[H, G, A] = Coproduct[H, G, A](Right(I.inj(a)))
    }
}
```

[^type_lambda1]: `Coproduct`の部分は実際、`({type λ[A] = Coproduct[F, G, A]})#λ`であるが、見やすさのためこのように表記した。

[^type_lambda2]: こちらも正しくは、`({type λ[A] = Coproduct[H, G, A]})#λ`であるが、見やすさのためこのように表記した。

先ほど`Coproduct`で作った`example`を次のように書きなおせる[^why_more]。

```scala:TwitterWithDelete.scala
def inject[A](a: Twitter[A])(implicit I: Inject[Twitter, TwitterWithDelete]) =
  I.inj(a)
def inject[A](a: DeleteOfTwitter[A])(implicit I: Inject[DeleteOfTwitter, TwitterWithDelete]) =
  I.inj(a)

val example2: Free[TwitterWithDelete, Unit] =
  more(inject(Update("new tweet", more(inject(Delete("<id>", done()))))))
```

[^why_more]: `more`の部分が繰り返し表われていて、これを取り除きたかったが、Scala上で上手く型を付けることができなかった。

さて、なんとかDSLを作ることができたので、後はこれのインタープリターを実装すればよい。

## インタープリター

CoproductやInjectを使っても、インタープリターは同じように書ける。

```scala:TwitterWithDeleteInterpreter.scala
def runTwitterWithDelete[A](dsl: Free[TwitterWithDelete, A], env: UseWSClient with UseOAuthCred): Unit = dsl match {
  case Done(a) => ()
  case More(x) => x.value match {
    case Left(a) => a match {
      case Fetch(screenName, f) =>
        for {
          fws <- fetchUserByScreenName(screenName).run(env)
        } yield runTwitterWithDelete(f(fws), env)
      case Update(status, next) =>
        for {
          _ <- updateStatus(status).run(env)
        } yield runTwitterWithDelete(next, env)
    }
    case Right(b) => b match {
      case Delete(id, next) => ???
    }
  }
}
```

ただ、これはFreeモナドとCoproductの入れ子構造がそのまま反映されており、もし`TwitterWithDelete`に対して別のものをさらにInjectした際に大変面倒になる。そこで`Twitter`と`DeleteOfTwitter`に対するそれぞれのインタープリターを**自然変換**を用いて合成するという方法もあるが、この記事では割愛する[^natural_transformation]。

[^natural_transformation]: この手法に興味がある方は、[Compositional application architecture with reasonably priced monads](https://gist.github.com/runarorama/a8fab38e473fafa0921d)が参考になる。

# Tagless Final

Tagless Finalとは、プログラム言語に埋め込みDSLのインタープリターを作るためなどに用いられる手法である。こちらの手法は今まで行ってきたFreeモナドやCoproductとは一線を画する手法である。

## InitialとFinal

この文章では次のような代数的データ型（ADT）を構築し、それのインタープリターを作成する伝統的な方法を**Initial**な方法と呼ぶ

> ```scala
> sealed trait Twitter[A]
> 
> case class Fetch[A](screenName: String, a: Future[WSResponse] => A) extends Twitter[A]
> case class Update[A](status: String, a: A) extends Twitter[A]
> ```

一方で、Tagless Finalではこのような代数的データ型を作成せずにインタープリターを構築する。Intialなアプローチと比較して次のような利点がある。

- ケースクラスのインスタンス化が必要ない
- GADT（一般化代数的データ型）が必要ない[^gadt]
- Expression Problemを回避することができる
- Higher-order Abstract Syntax（HOAS：高階抽象構文）[^hoas]を使うことができる

この記事では主にExpression Problemの回避に注目してInitialな方法と比較する。

[^gadt]: Scalaには一般化代数的データ型があるので、この部分は大きなメリットになり得ないかもしれない。他にこの機能を持つ言語として例えばOCamlやHaskell、Haxeがある。

[^hoas]: HOASについては後述する。

## Expression Problemの回避

Tagless FinalではFreeモナドなどを用いたInitialなアプローチで行なわれていたような、`Twitter`のような代数的データ型を定義しない。Tagless Finalでは型クラスを用いてDSLを表現する。

```scala:TwitterSYM.scala
trait TwitterSYM[R[_]] {
  def string(str: String): R[String]
  def fetch(screenName: R[String]): R[WSResponse]
  def getScreenName(str: R[WSResponse]): R[String]
  def update(status: R[String]): R[String]
}
```

これを用いて、実際のインタープリターを次のように実装する。

```scala:TwitterSYMInterpreter.scala
object TwitterSYMInterpreter {
  type Twitter[A] = Reader[UseWSClient with UseOAuthCred, A]

  implicit val twitterSYMInterpreter = new TwitterSYM[Twitter] {
    def string(str: String): Twitter[String] = pure(str)

    def fetch(screenName: Twitter[String]): Twitter[WSResponse] =
      for {
        sn <- screenName
        env <- ask
      } yield {
        Await.result(
          env.client.url("https://api.twitter.com/1.1/users/show.json")
            .withQueryString("screen_name" -> sn)
            .sign(env.cred)
            .get(),
          Duration.Inf
        )
      }
    
    def getScreenName(res: Twitter[WSResponse]): Twitter[String] =
      for {
        raw <- res
        env <- ask
      } yield (raw.json \ "screen_name").as[String]

    def update(status: Twitter[String]): Twitter[String] =
      for {
        s <- status
        env <- ask
      } yield {
        val res = Await.result(
          env.client.url("https://api.twitter.com/1.1/statuses/update.json")
            .sign(env.cred)
            .post(Map("status" -> Seq(s))),
          Duration.Inf
        )

        (res.json \ "id_str").as[String]
      }
  }
}
```

まず型`Twitter`を定義している。これまでのFreeモナドの例でも同じ名前の型が登場したが、それとは異なるので注意して欲しい。
Tagless Finalはこのように、インタープリターを型クラス`TwitterSYM`のインスタンスとして定義し、これらのインスタンスを呼び出すという形をとる。

```scala
def string(str: String)(implicit T: TwitterSYM[Twitter]): Twitter[String] =
  T.string(str)

def fetch(screenName: Twitter[String])(implicit T: TwitterSYM[Twitter]): Twitter[WSResponse] =
  T.fetch(screenName)

def getScreeName(res: Twitter[WSResponse])(implicit T: TwitterSYM[Twitter]): Twitter[String] =
  T.getScreenName(res)

def update(status: Twitter[String])(implicit T: TwitterSYM[Twitter]): Twitter[String] =
  T.update(status)
```

これだけでもはやDependency InjectionのためのDSLとしての機能を持っている。次のように使うことができる。

```scala
update(
  getScreeName(fetch(string("_yyu_")))
).run(DefaultEnvironment.defaultEnvironment)
```

さて、それではFreeの時のようにツイートを削除する機能を後から追加する。先ほど定義した`TwitterSYM`は型クラスなので、次のように新たな型クラスを追加するだけでExpression Problemを回避することができる。

```scala:DeleteSYM.scala
trait DeleteSYM {
  def delete(id: Twitter[String]): Twitter[Boolean]
}
```

そして、インタープリターもこれのインスタンスとして定義する。

```scala:DeleteSYMInterpreter.scala
object DeleteSYMInterpreter {
  type Twitter[A] = Reader[UseWSClient with UseOAuthCred, A]

  implicit val deleteInterpreter = new DeleteSYM[Twitter] {
    def delete(id: Twitter[String]): Twitter[Boolean] =
      for {
        idStr <- id
        env   <- ask
      } yield {
        val res = Await.result(
          env.client.url(s"https://api.twitter.com/1.1/statuses/destroy/${idStr}.json")
            .sign(env.cred)
            .post(Map("id" -> Seq(idStr))),
          Duration.Inf
        )

        res.status == 200
      }
  }

  def delete(id: Twitter[String])(implicit T: DeleteSYM[Twitter]): Twitter[Boolean] =
    T.delete(id)
}
```

次のように組み合せられる。

```scala
delete(
  update(
    getScreeName(fetch(string("_yyu_")))
  )
).run(DefaultEnvironment.defaultEnvironment)
```

このように、Tagless Finalは先ほどInjectなどを用いて行った処理の追加を比較的簡単に行うことができる。

## Higher-order Abstract Syntax

Higher-order Abstract Syntax（HOAS）とは、変数を束縛するような処理をターゲット言語[^target]に実装する際に、束縛する変数を対象言語のインタープリターなどが取り扱うのではなくて、ホスト言語（Scala）の機能を直接使って実装するテクニックのことである。
例えばこのDSLに変数を束縛して後の式で使うための構文`let`を使用して、OCamlのように書きたいとする。

```ocaml
let a = string("_yyu_") in
let b = fetch(a)        in
let c = getScreeName(b) in
let d = update(c)       in delete(d)
```

[^target]: 実装の対象となるプログラム言語を指し、この記事ではTwitter用のDSLに対応する。

このように`a`や`b`といった変数に処理の結果を束縛するような機能をDSLとして提供したい時にHOASは便利である。なぜなら、今回の例では変数名を全て別にしたが、実際にはある変数と同じ変数名が使われることがあり、それらを区別するためには[De Bruijn Index](https://ja.wikipedia.org/wiki/%E3%83%89%E3%83%BB%E3%83%96%E3%83%A9%E3%83%B3%E3%83%BB%E3%82%A4%E3%83%B3%E3%83%87%E3%83%83%E3%82%AF%E3%82%B9)などを用いてプログラムの中にある変数を数字へ変換する必要があるなど、変数束縛の処理は一般的に手間がかかる。ところが、HOASを用いれば変数はScalaの変数をそのまま用いるので、変数の管理をDSLのインタープリターやコンパイラーがする必要はない。
では、実際にTwitterのDSLにHOASの`let`文を用意する。まず、次のような型クラスを作る。

```scala:LetInSYM.scala
trait LetInSYM[R[_]] {
  def let[A, B](a: => R[A])(l: R[A => B]): R[B]
  def in[A, B](a: R[A] => R[B]): R[A => B]
}
```

そしてインタープリターを次のように実装する。

```scala:LetInSYMInterpreter.scala
object LetInSYMInterpreter {
  type Twitter[A] = Reader[UseWSClient with UseOAuthCred, A]

  implicit val letInInterpreter = new LetInSYM[Twitter] {
    def let[A, B](ta: => Twitter[A])(tf: Twitter[A => B]): Twitter[B] =
      for {
        a <- ta
        f <- tf
      } yield f(a)

    def in[A, B](f: Twitter[A] => Twitter[B]): Twitter[A => B] = {
      reader(e => (x: A) => f(pure(x)).run(e))
    }
  }

  def let[A, B](a: => Twitter[A])(f: Twitter[A => B])(implicit T: LetInSYM[Twitter]): Twitter[B] =
    T.let(a)(f)

  def in[A, B](f: Twitter[A] => Twitter[B])(implicit T: LetInSYM[Twitter]): Twitter[A => B] =
    T.in(f)
}
```

次のように用いる。

```scala
let (string("_yyu_")) (in (a =>
let (fetch(a))        (in (b =>
let (getScreeName(b)) (in (c =>
let (update(c))       (in (d =>
  delete(d)
)))))))).run(DefaultEnvironment.defaultEnvironment)
```

このように、変数を用いているにも関わらず、変数を取り扱う部分をインタープリターに書かなくてもよく実装が大変楽になる。

# Inject _vs_ Tagless Final

## Tagless Finalにおけるパターンマッチ

Freeモナドを用いた場合、`Fetch`や`Delete`といったDSLの命令に対応するケースクラスでパターンマッチができるが、一方でTagless Finalにはケースクラスに相当するものが存在しないので、木構造のデータを取り扱えないように一見すると思える。しかし、それについては解決策が存在する。これについて詳しく知りたい方は[Typed Tagless Final Interpreters](http://okmij.org/ftp/tagless-final/course/lecture.pdf)を参照して欲しい。

## Olegさんの指摘

Lambda-the-Ultimateというサイトに、[Tagless Finalの論文](http://okmij.org/ftp/tagless-final/JFP.pdf)を発表した著者の一人であるOlegさんによる[Expression problem solutions in Haskell](http://lambda-the-ultimate.org/node/4394#comment-68060)という投稿がある。

> Tagless-final approach also easily solves the expression problem, both in the first-order and higher-order cases. In the higher-order case, tagless-final permits (very convenient) higher-order abstract syntax. `Data Types a la Carte'[^data_type_a_la_carte] or other initial encodings cannot handle HOAS because of the contra-variant occurrences of the recursive data type. 

[^data_type_a_la_carte]: この記事の前部で触れたCoproductとInjectによるExpression Problemの回避法について述べた論文。

これによると、Coproductなどを用いたInitialなアプローチではHOASを取り扱えないと述べられている。再帰的なデータ型ではHOASを取り扱えないという根拠はよく分からないが、少なくともOlegさんはこのように主張している。

# まとめ

個人的な感想としては、Tagless Finalの方がInjectやCoproductを使ってDSLを構成するよりもシンプルに思える。この記事でInjectとTagless Finalの性能評価を行う予定であったが、記事が長くなったので次の機会にしようと思う。Tagless Finalを用いたDSLがDependency Injectionのために使われる未来もあるかもしれない。

# 参考文献

- [Free-ScalikeJDBC から見る合成可能なDSLの作り方](https://gist.github.com/gakuzzzz/147c520e32177fea75f0)
- [Compositional Application Architecture With Reasonably Priced Monads](https://dl.dropboxusercontent.com/u/4588997/ReasonablyPriced.pdf)
- [インタプリタ](https://github.com/Kinokkory/wiwinwlh-jp/wiki/%E3%82%A4%E3%83%B3%E3%82%BF%E3%83%97%E3%83%AA%E3%82%BF#hoas)
- [Typed Tagless Final Interpreters](http://okmij.org/ftp/tagless-final/course/lecture.pdf)
- [Data types à la carte](http://www.cs.ru.nl/~W.Swierstra/Publications/DataTypesALaCarte.pdf)
- [CoproductとInjectを使ったFree Monadの合成とExtensible Effects](http://d.hatena.ne.jp/xuwei/20140618/1403054751)
- [Finally Tagless, Partially Evaluated: Tagless Staged Interpreters for Simpler Typed Languages](http://okmij.org/ftp/tagless-final/JFP.pdf)
- [Dependency InjectionとDSL](http://qiita.com/yyu/items/a2debfcde8f1915d5083)
- [Expression problem solutions in Haskell](http://lambda-the-ultimate.org/node/4394#comment-68060)
- [関数型SCALA 型クラス編](http://halcat0x15a.github.io/slide/functional_scala/#/)
