# はじめに

[Play Framework](https://www.playframework.com/)にはcase classからJSONへ変換するためのインスタンスを自動で作るマクロがある。一方でなんらかの型をXMLへ変換する機能はない。そこでこの記事では、まずPlayがどのようにcase classをJSONへ変換しているのかを軽く解説してそれのXML版を作り、最後にScalaのマクロを用いてcase classからXMLを生成するためのインスタンスを自動生成する。

# Playが型`A`をJSONへ変換するとき

Playが型`A`をJSONへ変換する際には`Writes[A]`という[型クラス](http://halcat.org/slide/functional_scala/#/)のインスタンスを要求する。この`Writes`は次のような型クラスになっている。

> https://github.com/playframework/playframework/blob/master/framework/src/play-json/src/main/scala/play/api/libs/json/Writes.scala

```scala
trait Writes[-A] {
  /**
   * Convert the object into a JsValue
   */
  def writes(o: A): JsValue

  /**
   * Transforms the resulting [[JsValue]] using transformer function
   */
  def transform(transformer: JsValue => JsValue): Writes[A] = Writes[A] { a => transformer(this.writes(a)) }

  /**
   * Transforms resulting [[JsValue]] using Writes[JsValue]
   */
  def transform(transformer: Writes[JsValue]): Writes[A] = Writes[A] { a => transformer.writes(this.writes(a)) }
}
```

`transform`は`writes`から作られているので、ひとまずここでは無視すると、型クラス`Writes[A]`のインスタンスは次のようなメソッドを持つ。

```scala
def writes(o: A): JsValue
```

この`writes`は引数として型`A`の値`o`を取り、JSONを表す型`JsValue`を返しているので、`writes`は型`A`からJSONへ変換する関数であるといえる。例えば、Playでよく使う`Json.toJson`という関数は次のようになる。

> https://github.com/playframework/playframework/blob/master/framework/src/play-json/src/main/scala/play/api/libs/json/Json.scala#L118

```scala
def toJson[T](o: T)(implicit tjs: Writes[T]): JsValue = tjs.writes(o)
```

このように、implicitパラメーターで`Writes[T]`のインスタンスを受け取って、それを用いてJSONへの変換を行う。
これをそっくりXMLへ移植すればよい。

# 型`A`をXMLへ変換する型クラス`XmlWrites[A]`

JSONへ変換する際に用いた型クラス`Writes[A]`とほとんど同じ`XmlWrites[A]`を次のように定義する。ScalaにはXMLを表す型があらかじめ用意されているので、それをそのまま用いればよい。

```scala:XmlWrites.scala
trait XmlWrites[-A] {
  def writes(o: A): scala.xml.NodeSeq
}
```

そして、`Json.toJson`のような関数を定義する。

```scala:Xml.scala
object Xml {
  def toXml[W](o: W)(implicit X: XmlWrites[W]): scala.xml.NodeSeq = X.writes(o)
}
```

これは次のように使うことができる。

```scala
case class Test(a: String, b: Int)

implicit val testWrites: XmlWrites[Test] = new Writes[Test] {
  def writes(o: Test): NodeSeq =
    <a>
      {o.a}
    </a>
    <b>
      {o.b.toString}
    </b>
}

Xml.toXml(Test("hoge", 123))
```

やや冗長だが、これで一応動作はする。

# マクロを用いたインスタンスの自動生成

Playの`Writes`にはマクロを使ってcase classの`Writes`インスタンスを自動生成することができる。例えば先ほどの`Test`の`Writes`は次のように書ける。

```scala
case class Test(a: String, b: Int)

implicit val testJsonWrites: Writes[Test] = Json.writes[Test]

Json.toJson(Test("hoge", 123))
```

このように一行でインスタンスを生成できる。Playの実装を調べるとScalaのマクロを使ってインスタンスを生成していたので、[こちらの記事](http://matsu-chara.hatenablog.com/entry/2015/06/21/110000)を参考にしつつ、case classのインスタンスを自動生成するマクロを次のように実装する。

```scala:XmlWrites.scala
object Xml {
  def toXml[W](o: W)(implicit X: XmlWrites[W]): scala.xml.NodeSeq = X.writes(o)

  def xmlWrites[A]: XmlWrites[A] = macro XmlMacroImpl.impl[A]
}
```

```scala:XmlMacroImpl.scala
// macroでcase classのXmlWritesインスタンスを自動導出する
// http://matsu-chara.hatenablog.com/entry/2015/06/21/110000
object XmlMacroImpl {
  def impl[A: c.WeakTypeTag](c: blackbox.Context): c.Expr[XmlWrites[A]] ={
    import c.universe._

    // case classのクラス名
    val caseClassSym: c.universe.Symbol = c.weakTypeOf[A].typeSymbol
    if (!caseClassSym.isClass || !caseClassSym.asClass.isCaseClass) c.abort(c.enclosingPosition, s"$caseClassSym is not a case class")

    // 各フィールドのシンボル
    val syms: List[TermSymbol] = caseClassSym.typeSignature.decls.toList.collect { case x: TermSymbol if x.isVal && x.isCaseAccessor => x }

    val xmlTreeList: List[Tree] = syms.map { e =>
      val name = e.name.toString.trim
      val elemTree = q"_root_.scala.xml.Elem(null, $name, _root_.scala.xml.Null, _root_.scala.xml.TopScope, false, implicitly[XmlWrites[${e.typeSignature}]].writes(o.${TermName(name)}): _*)"
      q"$$removeEmptyNode($elemTree)"
    }

    val xmlTree: Tree = xmlTreeList.tail.foldLeft(xmlTreeList.head)((x, y) =>
      q"$x ++ $y"
    )

    val finalTree: Tree =
      q"""
        def $$removeEmptyNode(node: _root_.scala.xml.Elem): _root_.scala.xml.NodeSeq = node match {
          case _root_.scala.xml.Elem(_, _, _, _) => _root_.scala.xml.NodeSeq.Empty
          case _ => node
        }

        new XmlWrites[$caseClassSym] {
          def writes(o: $caseClassSym): scala.xml.NodeSeq = $xmlTree
        }
      """

    c.Expr[XmlWrites[A]](finalTree)
  }
}
```

case classかどうかを判定して、case classならばフィールドと型情報を取得し、それを使ってコードを組み立てていく。また、`$$removeEmptyNode`関数は`<a>NodeSeq.Empty</a>`のようなXMLノードが発生した際に、その要素を消去する関数である。

あとは、よく使いそうなインスタンスを`XmlWrites`のコンパニオンオブジェクトに用意しておく。

```scala:XmlWrites.scala
object XmlWrites {
  implicit val stringWrites: XmlWrites[String] = new XmlWrites[String] {
    def writes(o: String): NodeSeq = Text(o)
  }

  implicit val intWrites: XmlWrites[Int] = new XmlWrites[Int] {
    def writes(o: Int): NodeSeq = Text(o.toString)
  }

  implicit val floatWrites: XmlWrites[Float] = new XmlWrites[Float] {
    def writes(o: Float): NodeSeq = Text(o.toString)
  }

  implicit val doubleWrites: XmlWrites[Double] = new XmlWrites[Double] {
    def writes(o: Double): NodeSeq = Text(o.toString)
  }

  implicit val booleanWrites: XmlWrites[Boolean] = new XmlWrites[Boolean] {
    def writes(o: Boolean): NodeSeq = Text(o.toString)
  }

  implicit def listWrites[A](implicit W: XmlWrites[A]): XmlWrites[List[A]] = new XmlWrites[List[A]] {
    def writes(o: List[A]): NodeSeq = NodeSeq.fromSeq(o.flatMap(W.writes(_).toSeq))
  }

  implicit def optionWrites[A](implicit W: XmlWrites[A]): XmlWrites[Option[A]] = new XmlWrites[Option[A]] {
    def writes(o: Option[A]): NodeSeq = o match {
      case Some(a) => W.writes(a)
      case None => NodeSeq.Empty
    }
  }
}
```

これらを使えば、先ほどのcase class`Test`の`XmlWrites[Test]`は次のように生成できる。

```scala
case class Test(a: String, b: Int)

implicit val testJsonWrites: XmlWrites[Test] = Xml.xmlWrites[Test]

Xml.toXml(Test("hoge", 123))
```

# まとめ

この記事ではcase classからXMLへ変換する型クラスを用いて、XMLを生成し、かつインスタンスをマクロで生成するということを行った。はじめてのマクロにはいろいろ苦労したが、実用的なものが少ない行数で実装できてよかった。
