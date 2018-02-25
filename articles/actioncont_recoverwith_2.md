# はじめに

[ActionCont.recoverWithを作る](http://qiita.com/yyu/items/7b37b9a8ffca80c5ce96)では、`ActionCont.recoverWith`という次のような型を持つメソッドを作った。

```scala
def recoverWith[A](actionCont: ActionCont[A])(pf: PartialFunction[Throwable, ActionCont[A]])(implicit ec: ExecutionContext): ActionCont[A]
```

しかし、この関数には致命的な問題点があったので、この記事ではその問題点に関する説明と、回避するための方法について解説する。

# `ActionCont.recoverWith`の問題点

現在の`ActionCont.recoverWith`は次のように実装されている。

```scala
def fakeRun[A](actionCont: ActionCont[A])(implicit ec: ExecutionContext): Future[Result] =
  actionCont.run(value => Future.successful(Results.Ok))

def recoverWith[A](actionCont: ActionCont[A])(pf: PartialFunction[Throwable, ActionCont[A]])(implicit ec: ExecutionContext): ActionCont[A] =
  fromFuture(fakeRun(actionCont).map(_ => actionCont).recover(pf)).flatten
```

端的に述べると、`ActionCont.recoverWith`は後の継続を繰り返し呼ばないように配慮したが、`fakeRun`により、`ActionCont.recoverWith`に入力されたActionContを2回呼び出してしまう。前回の記事で出したような副作用がないような例であると問題がなく見えるが、副作用を入れた次のような例を作ると簡単に壊れてしまう[^contT]。

```scala
import scalaz.std.scalaFuture._

def add(x: Int, y: Int): ActionCont[Int] = ActionCont(k => k(x + y))

def sideEffect(): ActionCont[Unit] =
  ActionCont { k =>
    println("side effect")
    k(())
  }

val x = ActionCont.recoverWith(for {
  a <- add(1, 2)
  b <- sideEffect()
} yield
  Results.Ok("")
) {
  case _ =>
    ActionCont.successful(Results.Forbidden(""))
}

x.run_
```

[^contT]: この例ではActionContの実装に[Scalaz](https://github.com/scalaz/scalaz)の`IndexedContT`を使っているが、本質的な違いはない。

実行すると次のように、関数`sideEffect`で生成したActionContが2回実行されていることが分かる。

```
side effect
side effect
```

# 副作用に対して安全な`ActionCont.recoverWith`

次のように実装する。

```scala
def recoverWith[A](actionCont: ActionCont[A])(pf: PartialFunction[Throwable, ActionCont[A]])(implicit ec: ExecutionContext): ActionCont[A] = {
  class ResultContainer(val value: A) extends Result(header = ResponseHeader(200), body = Enumerator.empty)

  fromFuture(actionCont.run(value => Future.successful(new ResultContainer(value))).map {
    case r: ResultContainer => ActionCont[A](k => k(r.value))
    case r                  => ActionCont.result[A](Future.successful(r))
  }.recover(pf)).flatten
}
```

`run`は実行した場合は結果の型であるPlayの`Result`しか返すことができない。しかし、このようにまず`Result`型のサブタイプ`ResultContainer`を作っておき、それに継続を入れて、最後に`map`で値を取り出している。しかし、例えば`ActionCont.result`など継続を途中で破棄するような操作が行われている場合、我々が作った`ResultContainer`が返ってこない場合がある。そこでパターンマッチを用いて、継続が途中で破棄されるような場合はそのまま`ActionCont.result`で継続を破棄する。
以前の実装では実行して得られる値が`Future[Result]`という、`ActionCont.fakeRun`で適当に入力した使い物にならない値であったが、今回は`Future[A]`という入力されたActionContが次のActionContに渡すべき値（主作用）が手に入る。入力されたActionContはこの時点で既に実行された後なので、もう一度実行はせず、さきほど得られた値を次に渡すような最小のActionContを生成して返すことにする。
このようにすることで、もし入力されたActionContの中に副作用があったとしても、一度しか実行されないので問題とならないだろう。

# まとめ

このように、副作用を持つようなActionContに対しても安全にリカバーできるようになった。この記事を読んで、より良い実装を思いついた方は気軽にコメントして欲しい。
