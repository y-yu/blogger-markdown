---
title: ScalaにおけるGoogle Guiceと型クラスを併用した実装の限界
tags: Scala DI guice 関数型プログラミング
author: yyu
slide: false
---
# はじめに

Scalaでそれなりの規模のプログラムを書く場合、Dependency Injection（DI）を避けて通ることはほとんどできない。DIはクラスといった具体的な実装が依存する別の実装を外から注入するための手法であり、Javaで開発された[Google Guice](https://github.com/google/guice)がよく知られている。Scalaの特にWebプログラミングではGuiceを使うことが多いのではないかと思う。なぜならScalaのWebフレームワークとしてよく知られている[Play](https://www.playframework.com/)がデフォルトでGuiceを採用しているので、これに従って書くと自ずとGuiceで作っていくことになる。この記事ではGuiceと型クラスを組み合せた際に解決がやや難しい問題に直面することを示し、最善ではないが一応この問題への解決策を紹介する。また、この議論を通してGuiceの限界についても付け加える。
もしこの記事を読んでコメントなどがあれば、気軽にコメントなどで教えてほしい。
なお、この記事のコードは下記のリポジトリに置かれている。

- https://github.com/y-yu/guice-with-typeclass

# Guiceの限界とその問題点

いま次のようなクラスを考える。

```scala:NeedToBeInjected.scala
trait NeedToBeInjected

class NeedToBeInjectedImpl[A: HasTypeClass] @Inject() (
  dependency: Dependency
) extends NeedToBeInjected { }
```

ここでは簡単のためインターフェース`NeedToBeInjected`は空であり意味がないが、実際のコードでは`NeedToBeInjected`にインターフェースがあり、そして`NeedToBeInjectedImpl`に具体的な実装が書かれる。具体的な実装であるクラス`NeedToBeInjectedImpl`は別のインターフェースである`Dependency`[^dependency]に依存しており、この型を持つ具体的なインスタンスは`@Inject`によってGuiceから与えられる。ただ、ここで注意しなければならないのは`NeedToBeInjectedImpl`が型パラメータ`A`を取り、これは**コンテキスト境界**として型クラス`HasTypeClass`が与えられている。これは次のように書き直すことができる。

```scala
class NeedToBeInjectedImpl[A] @Inject() (
  dependency: Dependency
)(
  implicit a: HasTypeClass[A]
) extends NeedToBeInjected { }
```

[^dependency]: `Dependency`は他の依存なしにインスタンシエイトできる。

つまりこのクラス`NeedToBeInjectedImpl`は型クラスのインスタンス`HasTypeClass[A]`を探索し、見つかったときに限ってコンパイルを通過し実行することができる。型クラス`HasTypeClass`は下記のように任意の型`A`についてインスタンス`typeClassInstance`を定義した。

```scala:HasTypeClass.scala
trait HasTypeClass[A]

object HasTypeClass {
  implicit def typeClassInstance[A]: HasTypeClass[A] =
    new HasTypeClass[A] {}
}
```

さて、このコードを次のように配線[^wiring]した。ただし`Entity`は空のトレイトである。上述のように`HasTypeClass`は任意の型についてインスタンスが存在するので、`Entity`がどのような型であっても影響はないので、ここでは定義を省略する。

[^wiring]: DIのインターフェースと実装の関係を与えることを、ここでは**配線**という。

```scala:Module.scala
class Module extends AbstractModule {
  override def configure(): Unit = {
    bind(classOf[Dependency])
    bind(classOf[NeedToBeInjected])
      .to(new TypeLiteral[NeedToBeInjectedImpl[Entity]]() {})
  }
}
```

これを実行すると理想的には次のようにインスタンスが注入されるはずである。

<dl>
  <dt><code>Dependency</code></dt>
  <dd>Guiceによってインスタンスが注入される</dd>

  <dt><code>HasTypeClass</code></dt>
  <dd>Scalaコンパイラーによるimplicitパラメーター探索でインスタンスが注入される</dd>
</dl>

ところが実際に次のようなコードを実行すると次のようになる。

```scala:Main.scala
object Main {
  def main(args: Array[String]): Unit = {
    val injector = Guice.createInjector(new Module())

    injector
      .getInstance(
        Key.get(classOf[NeedToBeInjected])
      )
  }
}
```

```
sbt:guice-with-typeclass> run
[info] running Main
[error] (run-main-1) com.google.inject.CreationException: Unable to create injector, see the following errors:
[error]
[error] 1) No implementation for typeclass.HasTypeClass<entity.Entity> was bound.
[error]   while locating typeclass.HasTypeClass<entity.Entity>
[error]     for the 2nd parameter of impl.NeedToBeInjectedImpl.<init>(NeedToBeInjected.scala:11)
[error]   at module.Module.configure(Module.scala:11)
```

このようにScalaのimplicitパラメーターで注入されるべきインスタンスがGuiceによって注入されようとしており、かつGuiceはそれに失敗してランタイムエラーとなった。このように型クラスのインスタンスを取るような実装をGuiceでインスタンシエイトするためには、次のような方法を使う必要がある。

## 1. 型クラスのインスタンスを`bind`で配線する

Scalaの処理系がコンパイルを完了させたという時点で、implicitパラメーターの解決は終っている。しかしGuiceはそれを使ってくれないようなので、手作業でたとえば`HasTypeClass[Entity]`のような型クラスのインスタンスを配線しようという作戦である。

```scala:Module.scala
class Module extends AbstractModule {
  override def configure(): Unit = {
    bind(classOf[Dependency])
    bind(new TypeLiteral[HasTypeClass[Entity]]() {})
      .toInstance(implicitly[HasTypeClass[Entity]])
    bind(classOf[NeedToBeInjected])
      .to(new TypeLiteral[NeedToBeInjectedImpl[Entity]]() {})
  }
}
```

このように`HasTypeClass[Entity]`をGuiceのインターフェースと実装の「辞書」にも明示的に加えておけば無事に実行することができる。

## 2. 型パラメーターを固定した実装を継承で作成する

次のようにクラスの継承を利用して型パラメーターを決定しまうという作戦が次の作戦となる。

```scala:InjectTypeToResolveInstance.scala
class InjectTypeToResolveInstance @Inject() (
  dependency: Dependency
) extends NeedToBeInjectedImpl[Entity](dependency)
```

そしてこれの配線を次のように与える。

```scala
bind(classOf[NeedToBeInjected])
  .to(classOf[InjectTypeToResolveInstance])
```

こうすると無事にインスタンシエイトが可能となる。

# `bind`の方法 _vs_ 継承の方法

さて、ここからは（1）と（2）のメリット・デメリットを整理していきたい。筆者らが議論した結果、次のような結果となった。

- （1）`bind`の方法
    - 書くコード量が少ない
    - 一方で、Scalaの処理系が処理するimplicitパラメーターの処理をGuiceに任せるということになり、たとえば再帰的な型クラスがあった際に上手く動作するのか分からない
- （2）継承の方法
    - 書くコード量が（1）と比べて多いうえ、クラスが増える
    - しかしimplicitパラメーターの探索・注入をScala処理系が掌握することになる。これによってランタイムエラーの可能性を減らせる可能性がある

これらの議論に基づいて、筆者らは（2）がよいという結論になった。

# まとめ

このように、もともとJavaでの利用を想定したGuiceではScalaと完全に調和するのまだ無理があるのかもしれない。[マクロを使って`bind`を生成するというアイディア](https://twitter.com/_yyu_/status/1180772508275900416)もあり、これは今後の課題になりそうではある。
また[Airframe](https://github.com/wvlet/airframe)といったScala向けのDIツールを使ってみるというのも挙がったが、すでにGuiceを利用したコードが大量にあったため今回は検証せずに不採用とした。
DI方法を変更してよいという仮定のもとであれば、Cake patternのようなScalaを利用したコンパイルタイムDIであれば、この問題は本質的に発生しないと考えられる。GuiceなどのランタイムDIと、Cake patternなどのコンパイルタイムDIのうちどれを選ぶか？というのはしばしば議論されるが、Scalaにおいてはこのような型クラスの問題があることから、この一点だけにおいてはコンパイルタイムDIの方が有利ではないかと考えている。


# 謝辞

この記事の内容は@halcat0x15aさん、@xuwei_kさん、 @ma2k8さん、そして@ippei-takahashiさんとの議論によって洗練された。


