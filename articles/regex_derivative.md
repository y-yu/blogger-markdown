# はじめに

正規表現が文字列にマッチするかどうかを判定するプログラムを作るにあたっては、[以前の記事](http://qiita.com/yyu/items/84b1a00459408d1a7321)で紹介したようにVMを用いたり、または正規表現と等価なオートマトンを用いたりする。この記事ではこれらとは別の方法として「正規表現の微分（regular expression derivative）」を用いた方法について説明し、さらにこの方法を使うことで今までの方法では触れていなかった、正規表現のある一部にマッチした文字列を抽出する**サブマッチング**についても紹介する。
また、この記事で紹介するコードは次のGitHubリポジトリから入手できる。

> https://github.com/y-yu/PosixRegex

# 正規表現の抽象構文木

まずは、正規表現の抽象構文木を表す代数的データ型を次のように定義する。

```scala:data/Regex.scala
sealed trait Regex
object Regex {
  case class Var(n: String, r: Regex) extends Regex
  case class Let(l: Char) extends Regex
  case class Alt(r1: Regex, r2: Regex) extends Regex
  case class Star(r: Regex) extends Regex
  case class Con(r1: Regex, r2: Regex) extends Regex
  case object Epsilon extends Regex
  case object Empty extends Regex
}
```

一般的な定義と概ね同じだが、いくつか違うところもある。まず、サブマッチングに用いる変数を表す`Var`というコンストラクタが追加されている。これは`String`型で表した変数名と`Regex`型の正規表現を受け取り、与えられた変数名でサブパターンマッチを参照できるようにする。例えば、`Star(Var("x", Let('a')))`という正規表現に文字列`aaa`をマッチさせると、変数`x`には`a`が代入される。
また、`Epsilon`と`Empty`というよく似たようなオブジェクトがあるが、これらは次のような意味になる。

<dl>
  <dt><code>Epsilon</code></dt>
  <dd>空の文字にのみマッチする正規表現</dd>
  <dt><code>Empty</code></dt>
  <dd>どんな文字にもマッチしない正規表現</dd>
</dl>

# 文字列から正規表現の抽象構文木を作るパーザー

これは以前、@kmizuさんに紹介していただいた正規表現のパーザーを改造したが、ここでは文字列で表現された正規表現を先ほど定義した代数的データ型の表現へ変換することは、この記事の本質的な目標ではないのでリンクを紹介して例を挙げるのみとする。

https://github.com/y-yu/PosixRegex/blob/master/src/main/scala/RegexParser.scala

これを用いると、例えば次のような文字列で表した正規表現が次のような抽象構文木に変換される。

| 文字列で表現された正規表現 | 抽象構文木で表現された正規表現 |
|:------------------------:|:----------------------------:|
| $(a \mid b)*$ | `Star(Alt(Let(a),Let(b)))` |
| $(a \mid b \mid c)*d$ |`Con(Star(Alt(Alt(Let(a),Let(b)),Let(c))),Let(d))`|
| $(x:a*)b$ | `Con(Var(x,Star(Let(a))),Let(b))` |

# 正規表現の微分

正規表現の微分とは、まず`w:cw`という文字列があるとする。この文字列`w:cw`は文字`c`が文字列の先頭の一文字で、`cw`は文字列の先頭以外の残りを表す。ここで、もしある正規表現$r$が文字列`w:cw`にマッチするならば、正規表現$r$を文字`c`で**微分**した正規表現$r_c$は文字列`wc`にマッチする。このような正規表現$r_c$を見つける操作を正規表現の微分と言うことにする。
まず、正規表現を微分する関数を定義する前に、次のような補助関数`canEmpty`を定義する。

```scala:Helper.scala
object Helper {
  def canEmpty(r: Regex): Boolean = r match {
    case Epsilon => true
    case Let(_) => false
    case Alt(r1, r2) => canEmpty(r1) || canEmpty(r2)
    case Con(r1, r2) => canEmpty(r1) && canEmpty(r2)
    case Star(r) => true
    case Empty => false
    case Var(_, r) => canEmpty(r)
  }
}
```

この関数は、与えられた正規表現が空の文字列を受理するならば`true`を返し、そうでなければ`false`を返すという関数である。
この関数を用いて、微分する関数`derivative`は次のようなインターフェースを持つ。

```scala:Derivative.scala
object Derivative {
  def derivative(r: Regex, l: Char): Regex
}
```

正規表現`r`と文字`c`を受け取って、微分された正規表現を返す関数である。それでは`derivative`の具体的な実装をいくつか場合分けしながら考えていく。

## 簡単なものについて

次のケースについては直感的に決まる。

```scala
def derivative(r: Regex, l: Char): Regex = r match {
  case Empty => Empty
  case Epsilon => Empty
  case Let(c) => if (c == l) Epsilon else Empty
  case Var(_, r) => derivative(r, l)
}
```

`Var`はいわば正規表現に名前を付けているだけなので、中身の正規表現に対して微分を行う。

## 正規表現の“選択”について

正規表現の選択を表す$r_1 \mid r_2$の場合について考える。これは直感的に、正規表現$r_1$と$r_2$を微分してそれの選択を取ればよいので次のようになる。

```scala
def derivative(r: Regex, l: Char): Regex = r match {
  case Alt(r1, r2) => Alt(derivative(r1, l), derivative(r2, l))
}
```

## 正規表現の“連結”について

この場合はやや複雑だが、先ほど定義した`canEmpty`を用いて次のようになる。

```scala
def derivative(r: Regex, l: Char): Regex = r match {
  case Con(r1, r2) =>
    if (Helper.canEmpty(r1))
      Alt(Con(derivative(r1, l), r2), derivative(r2, l))
    else
      Con(derivative(r1, l), r2)
}
```

まず、連結された正規表現$r_1r_2$について考える。このプログラムの意味は、もし$r_1$が空であったら$r_2$を微分し、そうでなかったら$r_1$を微分するということでこのような定義となる。

## 正規表現の“繰り返し”について

正規表現$r\*$はやや考える必要がある。ナイーブな実装として、正規表現$r\* = \epsilon \mid rr*$を元に進めていくと、無限ループが発生してしまうためである。無限ループを回避するために、次のように定義する。

```scala
def derivative(r: Regex, l: Char): Regex = r match {
  case Star(r) => Con(derivative(r, l), Star(r))
}
```

# 正規表現と文字列のパーズツリー

さて、正規表現の微分をすることで、正規表現の**パーズツリー**を作れるようになる。このパーズツリーとは、正規表現とマッチさせる文字列によって構成されるものである。パーズツリーは次の代数的データ型で表現される。

```scala:data/ParseTree.scala
sealed trait ParseTree
object ParseTree {
  case object Void extends ParseTree
  case object Nil extends ParseTree
  case class Lit(l: Char) extends ParseTree
  case class Pair(t1: ParseTree, t2: ParseTree) extends ParseTree
  case class Left(t: ParseTree) extends ParseTree
  case class Right(t: ParseTree) extends ParseTree
  case class Cons(t: ParseTree, ts: ParseTree) extends ParseTree
}
```

このままでは表示が大変なので、このパーズツリーを表示するプリティプリンター`pp`を次のように定義する。

```scala:Helper.scala
object Helper {
  def pp(t: ParseTree): String = t match {
    case Void => "()"
    case Nil => "nil"
    case Lit(l) => s"$l"
    case Pair(t1, t2) => s"(${pp(t1)}, ${pp(t2)})"
    case Left(t) => s"Left(${pp(t)})"
    case Right(t) => s"Right(${pp(t)})"
    case Cons(v, vs) => s"${pp(v)}: ${pp(vs)}"
  }
}
```

例えば正規表現$(a \mid b)*$に文字列`ab`をマッチさせたとすると、次のようなパーズツリーが生成される。

```
Left(a): Right(b): nil
```

これは、まず正規表現$(a \mid b)$の選択の左側（`Left`）に`a`がマッチし、次に右側（`Right`）に`b`がマッチした、ということを示している。文字列と正規表現を使って、このパーズツリーを作るには先ほどの微分を使うことができる。

# パーズツリーの生成

まず、先ほど紹介した正規表現の微分は、文字列を一文字ずつ取り出していって、その一文字ずつで正規表現を徐々に削っていくような処理であった。

```math
r_0 \xrightarrow{l_1} r_1 \xrightarrow{l_2} r_2 \xrightarrow{l_3} \cdots \xrightarrow{l_n} r_n
```

パーズツリーはまず正規表現の微分を繰り返して、最終的な正規表現のパーズツリーを生成し、そこから一文字ずつ木に対して文字を**挿入**していくことでパーズツリーを組み立てる。

```math
v_0 \xleftarrow{l_1} v_1 \xleftarrow{l_2} v_2 \xleftarrow{l_3} \cdots \xleftarrow{l_n} v_n
```

まずは、この上の図で表現するところの$v_n$に対応するパーズツリーを得る関数`makeEps`を次のように定義する。

```scala:Parse.scala
object Parse {
  private def makeEps(r: Regex): ParseTree = r match {
    case Star(_) => ParseTree.Nil
    case Con(r1, r2) => Pair(makeEps(r1), makeEps(r2))
    case Alt(r1, r2) =>
      if (Helper.canEmpty(r1))
        Left(makeEps(r1))
      else if (Helper.canEmpty(r2))
        Right(makeEps(r2))
      else
        throw new RuntimeException("error of he alternation in makeEps")
    case Epsilon => Void
    case e => throw new RuntimeException(s"error in makeEps: $e")
  }
}
```

この関数`makeEps`は与えられた正規表現$r$が空を受理するならば、最初のパーズツリーを返す関数である。なぜ正規表現$r$が空を受理すると仮定しているかというと、先ほど述べたようにこの`makeEps`は微分を繰り返して文字列が尽きた時の正規表現が入力される。もし入力が尽きた時の正規表現が空を受理しないならば、正規表現のマッチングに失敗していると言えるので、パーズツリーを作ることができない。従ってこのような仮定をしている。

次に、このようにして得られた最初のパーズツリーに一文字ずつ文字を挿入していく関数`inject`を次のように定義する。

```scala:Parse.scala
object Parse {
  private def inject(r: Regex, l: Char, t: ParseTree): ParseTree = (r, t) match {
    case (Var(_, r), t) => inject(r, l, t)
    case (Star(r), Pair(v, vs)) => Cons(inject(r, l, v), vs)
    case (Con(r1, r2), t) => t match {
      case Pair(v1, v2) => Pair(inject(r1, l, v1), v2)
      case Left(Pair(v1, v2)) => Pair(inject(r1, l, v1), v2)
      case Right(v2) => Pair(makeEps(r1), inject(r2, l, v2))
      case e => throw new RuntimeException(s"error of the concatenation in inject: $e")
    }
    case (Alt(r1, r2), t) => t match {
      case Left(v1) => Left(inject(r1, l, v1))
      case Right(v2) => Right(inject(r2, l, v2))
      case e => throw new RuntimeException(s"error of the alternation in inject: $e")
    }
    case (Let(c), Void) => if (l == c) Lit(l) else throw new RuntimeException(s"error of the Letter in inject")
    case e => throw new RuntimeException(s"error in inject: $e")
  }
}
```

これの説明はやや複雑なので、詳細を知りたい場合は参考文献[^posix_regex]を参考にして欲しい。

[^posix_regex]: [POSIX Regular Expression Parsing with Derivatives](http://www.home.hs-karlsruhe.de/~suma0002/publications/regex-parsing-derivatives.pdf)

これを用いて、最終的にパーズツリーを生成する関数`parse`を次のように定義する。

```scala:Parse.scala
object Parse {
  def parse(r: Regex, str: Word): Try[ParseTree] =
    str match {
      case Nil if Helper.canEmpty(r) => Try(makeEps(r))
      case l::w => parse(Derivative.derivative(r, l), w).map(t => inject(r, l, t))
      case e => Try(throw new RuntimeException(s"error in parse: $e"))
    }
}
```

# サブマッチング

パーズツリーと正規表現から次のような関数`submatch`を用いてサブマッチングを行うことができる。

```scala:Submatch.scala
object Submatch {
  type Word = List[Char]

  private def flatten(t: ParseTree): Word = t match {
    case Void | Nil => List()
    case Left(v) => flatten(v)
    case Right(v) => flatten(v)
    case Cons(v, vs) => flatten(v) ++ flatten(vs)
    case Pair(v1, v2) => flatten(v1) ++ flatten(v2)
    case Lit(l) => List(l)
  }

  def submatch(t: ParseTree, r: Regex): Set[Map[String, Word]] = (t, r) match {
    case (Void, Epsilon) => Set.empty
    case (Lit(l), Let(c)) => if (l == c) Set.empty else throw new RuntimeException("error in submatch")
    case (Nil, Star(_)) => Set.empty
    case (Cons(v, vs), Star(r)) => submatch(v, r) ++ submatch(vs, Star(r))
    case (Pair(v1, v2), Con(r1, r2)) => submatch(v1, r1) ++ submatch(v2, r2)
    case (Left(v), Alt(r1, _)) => submatch(v, r1)
    case (Right(v), Alt(_, r2)) => submatch(v, r2)
    case (v, Var(n, r)) => Set(Map(n -> flatten(v))) ++ submatch(v, r)
    case e => throw new RuntimeException(s"error in submatch: $e")
  }
}
```

まず、`flatten`はパーズツリーを文字列だけにする関数である。これを使って、正規表現の中に変数`Var`がある場合はそれに対応するパーズツリーを`flatten`したものを追加するということをしている。
最後に、正規表現とマッチする文字列をコマンドライン引数から取れるようにして完成である。

```scala:Main.scala
object Main {
  def main(args: Array[String]): Unit = {
    val regex = RegexParser.parse(args(0))
    println(regex)

    val tree = regex.flatMap(Parse.parse(_, args(1).toCharArray.toList))
    println(tree.map(Helper.pp))

    for {
      r <- regex
      t <- tree
    } yield println(Submatch.submatch(t, r))
  }
}
```

これを用いて、正規表現$((x:a\*) \mid (b \mid c)\*)\*$に文字列`abaacc`をマッチさせると次のような結果となる。

```
Success(Star(Alt(Var(x,Star(Let(a))),Star(Alt(Let(b),Let(c))))))
Success(Left(a: nil): Right(Left(b): nil): Left(a: a: nil): Right(Right(c): Right(c): nil): nil)
Set(Map(x -> List(a)), Map(x -> List(a, a)))
```

一番上が文字列から抽象構文木へ変換した正規表現であり、二番目がパーズツリー、そして一番下がサブマッチングである。

# まとめ

正直、論文の全部を理解したわけではないが、ひとまずサブマッチングを搭載した正規表現のマッチングプログラムを書くことができた。論文ではさらに性能を向上させるためのテクニックが紹介されていたが、今回の記事ではナイーブな実装のみを紹介することにした。オートマトンやVMを使わずに正規表現のマッチングプログラムを書くことができて、よい経験となったと思う。

# 参考文献

- [POSIX Regular Expression Parsing with Derivatives](http://www.home.hs-karlsruhe.de/~suma0002/publications/regex-parsing-derivatives.pdf)
- [WORD Best Selection V](http://www.word-ac.net/)
