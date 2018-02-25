
**よりよい実装を作りました。**
→ http://qiita.com/yyu/items/bd6e205e801fb653a9cc


# はじめに

**ActionCont**とは継続モナド`Cont[R, A]`の型`A`に[Play](https://www.playframework.com/)のコントローラーの結果を表す型`Result`を組み合わせた`Cont[Future[Result], A]`のことである。このActionContは継続モナドの力を用いて柔軟にコントローラーを合成するために用いられる。この記事ではまず、このActionContについて軽く紹介した後に、既存のActionContではカバーできない点について言及し、それを解決するために今回作成した`ActionCont.recoverWith`について説明する。

# ActionContとエラー処理

ActionContとは“[継続モナドを使ってWebアプリケーションのコントローラーを自由自在に組み立てる](http://qiita.com/pab_tech/items/fc3d160a96cecdead622)”で導入された**継続モナド**の一種である。このActionContにはエラーを処理するための`recover`という関数が用意されており、それは次のようになっている。

```scala
object ActionCont { 
  def recover[A](actionCont: ActionCont[A])(pf: PartialFunction[Throwable, Future[Result]])(implicit executor: ExecutionContext): ActionCont[A] =
    ActionCont(f => actionCont.run(f).recoverWith(pf))
  }
}
```

これは、次のように使うことができる。

```scala
def getPostParameter(request: Request[AnyContent]): ActionCont[PostParameters] = ???

for {
  postParameters <- ActionCont.recover(getPostParameter(request)){
    case NonFatal(e) =>
      Future.successful(Results.BadRequest("error!"))
  }
} yield ???
```

これはエラー（つまりは`Future.failed(???)`）が発生し次第、即`Future[Result]`の値を打ち返して以降の処理をストップする。これはこれで良いが、`ActionCont.recover`だけではカバーできない状況がある。

# `ActionCont.recover`では難しいこと

ただし、エラーの中には回復可能なものがある。例えば次のような処理を考える。

1. クエリパラメーターからCSRFトークンを取得する
    - 成功したら後続にCSRFトークンを渡す
2. (1)に失敗したら、リクエストボディからJSON形式でCSRFトークンを取得する
3. (2)に失敗したら、`Results.BadRequest`となる

このような処理を書きたい場合、`ActionCont.recover`を用いたとしても、直ちに`Result`になってしまうので実現できない。そこで、次のようなインターフェースを持つ`ActionCont.recoverWith`を作成する。

```scala
def recoverWith[A](actionCont: ActionCont[A])(pf: PartialFunction[Throwable, ActionCont[A]])(implicit ec: ExecutionContext): ActionCont[A] =
```

`ActionCont.recover`とは部分関数として受けとる値の型が変っている。`ActionCont.recover`が`PartialFunction[Throwable, Future[Result]]`であるのに対して、`ActionCont.recoverWith`では`PartialFunction[Throwable, ActionCont[A]]`となっている。これがあれば、先ほどの処理は次のように書くことができる。

```scala
def getCsrfTokenFromQueryParameter(request: Request[AnyContent]): ActionCont[CsrfToken] = ???

def getCsrfTokenFromRequestBody(request: Request[AnyContent]): ActionCont[CsrfToken] = ???

for {
  csrfToken <- ActionCont.recoverWith(getCsrfTokenFromQueryParameter(request)) {
    case NonFatal(e) =>
      getCsrfTokenFromRequestBody(request)
  }
} yield ???
```

この`ActionCont.recoverWith`をどのように実装すればよいだろうか。

# 仮の継続を渡して`ActionCont`を実行する`fakeRun`

まず、継続モナドについておさらいしておくと、継続モナドは「後続の処理を受け取って、それを使って処理を行う」という能力を持つ。そのため、`ActionCont.recoverWith`の実装としてシンプルに次のような実装を思いつく。

1. 失敗するかもしれない`ActionCont`に継続を渡して実行する
    - もし成功したら、この`ActionCont`を使う
2. 失敗したら、代わりの`ActionCont`に継続を渡す

すると、この実装では継続を合計で**2回**実行していることになる。確かにCSRFトークンを取得する処理ならば2回実行したところで問題はなさそうだが、もし後続の処理（継続）に「データベースに書き込む」といった副作用を伴う処理があったとしたら大変まずいことになってしまう。なので、ここではやや不完全になることが予想されるが、次のような実装を行うことにする。

1. 失敗するかもしれない`ActionCont`に**仮の継続**を渡して実行する
    - もし成功したら、この`ActionCont`に本物の継続を渡す
2. 失敗したら、代わりの`ActionCont`に継続を渡す

この仮の継続を渡す関数`fakeRun`は次のように定義する。

```scala
def fakeRun[A](actionCont: ActionCont[A])(implicit ec: ExecutionContext): Future[Result] =
  actionCont.run(value => Future.successful(Results.Ok))
```

これを使えば、`ActionCont.recoverWith`を作ることができる。

# `ActionCont.recoverWith`を作る

次のような定義になる。

```scala
def recoverWith[A](actionCont: ActionCont[A])(pf: PartialFunction[Throwable, ActionCont[A]])(implicit ec: ExecutionContext): ActionCont[A] =
  fromFuture(fakeRun(actionCont).map(_ => actionCont).recover(pf)).flatten
```

まず、`fakeRun(actionCont)`で受け取った`ActionCont`を仮に実行している。そして、その結果が成功であったとしたら`map`で結果を捨てつつ元の`ActionCont`を返している。もし結果がエラー（`Future.failed(???)`）だとしたら、`Future.recover`と受け取った部分関数`pf`で`ActionCont`にしている。すると、`Future[ActionCont[A]]`という型の値が得られるので、これを`fromFuture`[^fromFuture]で`ActionCont[ActionCont[A]]`にする。あとは二重になった`ActionCont`を`flatten`で削れば最終的に`ActionCont[A]`となる。

[^fromFuture]: [継続モナドを使ってWebアプリケーションのコントローラーを自由自在に組み立てる](http://qiita.com/pab_tech/items/fc3d160a96cecdead622)を参照。

# `ActionCont.recoverWith`の課題

上で述べたように、`ActionCont.recoverWith`に渡されるActionContは`fakeRun`で実行するので、**後続の処理の結果によってエラーを出す**ようなActionContに対して使うと思わぬ挙動をする可能性がある。しかし、僕の考える限り後続の処理の結果によってエラーを出すという状況があまり考えられなかったので、実用上は問題にならないと思われる。

# まとめ

やや課題が残ったものの、これによって失敗したら別のActionContに差し換えるという操作を実装することができた。もしこれより良い方法を思いついた方がいらっしゃれば、気軽にコメントなどで教えて欲しいと思う。
