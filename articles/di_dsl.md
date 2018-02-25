[Dead-Simple Dependency Injection in Scala](https://speakerdeck.com/marakana/dead-simple-dependency-injection-in-scala)という発表で、Dependency Injection（依存の注入）を[Readerモナド](http://itpro.nikkeibp.co.jp/article/COLUMN/20090303/325807/)などを用いて行うという技術があった。下記がその発表である。

[![](https://img.youtube.com/vi/ZasXwtTRkio/0.jpg)](https://www.youtube.com/watch?v=ZasXwtTRkio)

この記事ではまず、Dependency Injectionについての説明と、Readerモナドについての説明を行い、次にReaderモナドを使ったDependency Injectionについて述べて、[Freeモナド](http://d.hatena.ne.jp/fumiexcel/20121111/1352614885)を用いて小さな[DSL](https://ja.wikipedia.org/wiki/%E3%83%89%E3%83%A1%E3%82%A4%E3%83%B3%E5%9B%BA%E6%9C%89%E8%A8%80%E8%AA%9E)を作るアプローチを紹介する。
この記事はモナドやDependency Injectionなどに関する前提知識がなくてもある程度読めるように意図しているが、Scalaの文法的な知識を前提としている。また、もし説明が不足している点や文章の意図が分かりにくい部分があれば、気軽にコメントなどで指摘して欲しい。

> 注意：
> 記事の中にあるコードは読みやすさのために`import`などを省略しているので、このままでは動かない。動かしたい方は[Githubのリポジトリ](https://github.com/yoshimuraYuu/DIwithTaglessFinal)を使うとよい。

# ReaderモナドとDependency Injection

例えば次のようにTwitterから情報を取ってきたり、ツイートを投稿する関数があるとする。

```scala:TwitterRepository.scala
object TwitterRepository {
  val config = new NingAsyncHttpClientConfigBuilder(DefaultWSClientConfig()).build()
  val builder = new AsyncHttpClientConfig.Builder(config)
  val client = new NingWSClient(builder.build)

  val key   = ConsumerKey(
    "key",
    "secret"
  )
  val token = RequestToken(
    "token",
    "secret"
  )

  def fetchUserByScreenName(screenName: String): Future[WSResponse] =
    client.url("https://api.twitter.com/1.1/users/show.json")
      .withQueryString("screen_name" -> screenName)
      .sign(OAuthCalculator(key, token))
      .get()

  def updateStatus(status: String): Future[WSResponse] =
    client.url("https://api.twitter.com/1.1/statuses/update.json")
      .sign(OAuthCalculator(key, token))
      .post(Map("status" -> Seq(status)))
}
```

これで動きはするが、外部と通信する部分（`client`）やTwitterの鍵（`key`）やトークン（`token`）がハードコードされているので、別のアカウントに差し換えたり、テストする際に不便なことになる。
そこで**Readerモナド**を使って外から依存を注入しようというのがDead-Simple Dependency Injection in Scalaなどで紹介されている手法である。

## Readerモナド

まず、Readerモナド `Reader`を次のように定義する[^covariance]。

[^covariance]: この`Reader`は単純化のため共変や反変のパラメータを省略している。

```scala:Reader.scala
case class Reader[E, A](g: E => A) {
  def apply(e: E) = g(e)
  def run: E => A = apply
  def map[B](f: A => B): Reader[E, B] = Reader(e => f(g(e)))
  def flatMap[B](f: A => Reader[E, B]): Reader[E, B] = Reader(e => f(g(e))(e))
}

object Reader {
  def pure[E, A](a: A): Reader[E, A] = Reader(e => a)
  def ask[E]: Reader[E, E] = Reader(identity)
  def local[E, A](f: E => E, c: Reader[E, A]): Reader[E, A] = Reader(e => c(f(e)))
  def reader[E, A](f: E => A): Reader[E, A] = Reader(f)
}
```

`Reader`について全てを説明するのは大変なので、ここでは直感的なことだけを説明する。まず、`Reader`の`map`と`flatMap`に注目すると、今の`Reader`が持っている関数`g`に`e`を与えて実行し、それを使って`f`を実行するという操作をする関数を持つ新しい`Reader`を生成している。ただし、`map`や`flatMap`の際には`f`と`g`を組合せるだけで、実際に実行するのは`apply`もしくは`run`[^why_run]を用いて引数`e`に値を投入した時に初めて全ての計算が実行されることになる。
次に[コンパニオンオブジェクト](http://www.ne.jp/asahi/hishidama/home/tech/scala/object.html#h_companion_object)`Reader`で定義しているものについて説明する。

[^why_run]: この`run`は`apply`と全く同じだが、Readerモナドに環境を入れて実行する際には`run`というような名前の関数が用いられることが多いので、今回は慣習を引き継いでこちらのメソッドも用意した。`run`も`apply`も同じ意味である。

<dl>
  <dt><code>pure</code></dt>
  <dd>任意の値を<code>Reader</code>にする</dd>
  <dt><code>ask</code></dt>
  <dd>環境<code>e</code>を取得する</dd>
  <dt><code>local</code></dt>
  <dd>環境<code>e</code>を書き換える</dd>
  <dt><code>reader</code></dt>
  <dd>関数を<code>Reader</code>にする</dd>
</dl>

これらの説明は今はよく分からないかもしれないが、後で実際に使う際に具体的な例として表われるので心配ない。

## Readerモナド vs 関数

一見するとReaderモナドは関数（ラムダ式）とほとんど同じように思える。しかし、大きな違いとして、Readerモナドは自身が持つ関数に共通の**環境**というグローバル変数でもなくローカル変数でもない第三の場所を提供する[^environment]。関数の中から何か情報を参照したい場合、通常は次の二択になる。

- 引数で渡す
- グローバル変数から読み出す

グローバル変数を用いることが不味いというのはよく知られているが、かといって引数を使うアプローチも、次のように関数がいくつも連なった状況を考えると問題が浮き彫りになる。

```scala
def main(args: Array[String]) = {
  ???
  level1(args[0])
}

def level1(d: String) = {
  ???  // ここでは d を使わない
  level2(d)
}

def level2(d: String) = {
  ???  // ここでは d を使わない
  need_arg(d)
}

def need_arg(d: String) =
  ??? // d を必要とする
```

このようにある関数が依存してる関数の依存をわざわざ明示的に引数で渡す必要があるので、引数が増えて混乱したり、コードの見通しが悪くなったりする。また、依存が増えた際に関係する関数の引数を全て増やす必要がある。
一方で、Readerモナドは共通に使う情報を引数でもグローバル変数でもない第三の場所（環境）に入れることで、グローバル変数と引数で一長一短だと思われていた問題をスマートに解決する。

[^environment]: 通常「環境」という言葉はローカル変数もグローバル変数も含んだものを指すと思うが、この記事ではReaderモナドが提供する環境という意味でのみこの言葉を使うことにする。

## Dependency Injection

具体的な例で、 Readerモナドを用いたDependency Injectionがどのように行われるのだろうか。

まず、依存を持つことを表すトレイトを用意する。

```scala:UseWSClient.scala
trait UseWSClient {
  val client: WSClient
}
```

```scala:UseOAuthCred.scala
trait UseOAuthCred {
  val cred: OAuthCalculator
}
```

`TwitterRepository`を改造して、Readerモナドを返すようにする。また、環境として先程定義したトレイト`UseWSClient`と`UseOAuthCred`を`with`で結合したものを用いる。

```scala:TwitterRepositoryDI.scala
object TwitterRepositoryDI {
  def fetchUserByScreenName(screenName: String): Reader[UseWSClient with UseOAuthCred, Future[WSResponse]] =
    reader(env =>
      env.client.url("https://api.twitter.com/1.1/users/show.json")
        .withQueryString("screen_name" -> screenName)
        .sign(env.cred)
        .get())

  def updateStatus(status: String): Reader[UseWSClient with UseOAuthCred, Future[WSResponse]] =
    reader(env =>
      env.client.url("https://api.twitter.com/1.1/statuses/update.json")
        .sign(env.cred)
        .post(Map("status" -> Seq(status))))

}
```

そして、依存を保存しておく場所を作る。

```scala:DefaultEnvironment.scala
object DefaultEnvironment {
  val config  = new NingAsyncHttpClientConfigBuilder(DefaultWSClientConfig()).build()
  val builder = new AsyncHttpClientConfig.Builder(config)
  val c       = new NingWSClient(builder.build)

  val defaultEnvironment = new UseWSClient with UseOAuthCred {
    val client = c
    val cred = OAuthCalculator(
      ConsumerKey(
        "key",
        "secret"
      ),
      RequestToken(
        "token",
        "secret"
      )
    )
  }
}
```

最終的には次のように実行する。

```scala
fetchUserByScreenName("_yyu_").run(DefaultEnvironment.defaultEnvironment)
```

このように、Readerモナドの環境として依存を注入できるうえ、これらのReaderを合成することもできる[^why_compose]。

```scala
(for {
  _ <- fetchUserByScreenName("_yyu_")
  _ <- updateStatus("good")
} yield () ).run(DefaultEnvironment.defaultEnvironment)
```

[^why_compose]: 今回の例では合成する意味は全くないが……。

## 依存の選択

例えば次のよう`Future[Boolean]`を返すような例と、その結果に応じてどの依存を使うのかを選択して注入する例を考えてみることにする。
まずは次のような関数を用意する。

```scala:TwitterRepositoryDI.scala
def existUserWithScreenName(screenName: String): Reader[UseWSClient with UseOAuthCred, Future[Boolean]] =
  reader(env =>
    for {
      res <- env.client.url("https://api.twitter.com/1.1/users/show.json")
               .withQueryString("screen_name" -> screenName)
               .sign(env.cred)
               .get()
    } yield res.status == 200
  )
```

この関数は`screenName`を持つユーザーが存在するかどうかを判定する関数である。

次に`defaultEnvironment`とは別の依存を用意する。

```scala:DefaultEnvironment.scala
val adminEnvironment = new UseWSClient with UseOAuthCred {
  val client = c
  val cred = OAuthCalculator(
    ConsumerKey(
      "key",
      "secret"
    ),
    RequestToken(
      "token",
      "secret"
    )
  )
}
```

そして、環境を変更してReaderモナドを実行する`local`を使って次のようにする。

```scala
(for {
   fb <- existUserWithScreenName("_yyu_")
   _  <- local(
           (e: UseWSClient with UseOAuthCred) =>
             if (Await.result(fb, Duration.Inf))
               DefaultEnvironment.adminEnvironment
             else
               e,
           updateStatus("test")
         )
} yield () ).run(DefaultEnvironment.defaultEnvironment)
```

このコードでは、“\_yyu\_”というユーザーが存在すれば環境を`adminEnvironment`へ変更してから`updateStatus`を実行し、そうでなけば通常の環境で実行する。
このように、この方法では依存を実行時の値によって切り換えるといった柔軟な処理ができる。

# DSLとFreeモナド

計算を合成したりしつつ、依存を注入できるようになった。これを使ってTwitterを操作するためのミニプログラム言語（DSL）を作ろうというのが、Dead-Simple Dependency Injection in Scalaの後半パートになる。

## 小さなDSL

このTwitterの例では次のように、「次の計算」を持てるようなケースクラスとトレイトを用意する。

```scala:Twitter.scala
sealed trait Twitter[A]

case class Fetch[A](screenName: String, next: WSResponse => A) extends Twitter[A]
case class Update[A](status: String, next: A) extends Twitter[A]
```

次の計算は型`A`の`next`である。例えばユーザー情報を取得して、取得できた場合はツイートするという処理をこのように書きたい。

```scala
Fetch(
  "_yyu_",
  (fws: Future[WSResponse]) => {
    val ws = Await.result(fws, Duration.Inf)
    if (ws.status == 200)
      Update("exist", ())
    else
      Update("not exist", ())
  }
)
```

あとは各ケースクラスに対応する処理を書けばよいように思える。

```scala
def twitter_interpreter[A](a: Twitter[A]) = a match {
  case Fetch(user, next) =>
    for {
      res <- fetchUserByScreenName(user)
    } yield twitter_interpreter(next(res))

  case Update(status, next) =>
    for {
      _ <- updateStatus(status)
    } yield twitter_interpreter(next)
}
```

しかし、実はこれは上手くいかない。なぜなら`Fetch`や`Update`の持つ`next`の型は`A`であって`Twitter[A]`ではない。では`A`を`Twitter[A]`にすれば動くかというと、そうでもない。もし`next`が`Twitter[A]`だとすると、`Fetch`は次のようになる。

```scala
case class Fetch[A](screenName: String, next: WSResponse => Twitter[A]) extends Twitter[Twitter[A]]
```

このように`Fetch`の型が`Twitter[Twitter[A]]`となり、`Twitter`が二重になってしまって大変扱いづらい。
そこで、Dead-Simple Dependency Injection in Scalaでは**Freeモナド**を使ってこの問題を解決する。

## ファンクターとFreeモナドとインタープリター

Freeモナドは`Twitter[Twitter[A]]`のような構造を`Free[Twitter, A]`というFreeモナドへ落すデータ構造の一つである。これは、例えば`Twitter[Twitter[Twitter[Twitter[A]]]]`のようにどれだけネストしていたとしても全てが`Free[Twitter, A]`になる[^the_perfect_insider]。
このように便利なFreeモナドだが、この効能を得るためにFreeモナドは「`Twitter`が**ファンクター**である」という性質を要求する。

[^the_perfect_insider]: [The Perfect Insider](http://www.amazon.co.jp/dp/4062639246)

### ファンクター

ある型`F`がファンクターであるとは、`Twitter`は次のような型を持つ関数`map`を定義できるということである。

```scala:Functor.scala
trait Functor[F[_]] {
  def map[A, B](a: F[A])(f: A => B): F[B]
}
```

さらに、関数`map`は次の**ファンクター則**に則っていなければならない。

1. `map`の`f`に`x => x`を入れて生成されたものが、元の値と等しい
    - `assert( t.map(x => x) == t )`
2. 適当な関数`g`と`h`について、`g`と`h`の合成関数（`x => g(h(x))`）で`map`した値と、`h`で`map`した値を`g`で`map`した値が等しい
    - `assert( t.map(x => g(h(x))) == t.map(h).map(g) )`

このような制約を持つ`map`を`Fetch`や`Update`に対してどのように定義すればいいだろうか。少々天下り的だが、次のようにすればよい。

```scala
implicit val twitterFunctor = new Functor[Twitter] {
  def map[A, B](a: Twitter[A])(f: A => B) = a match {
    case Fetch(screenName, next) => Fetch(screenName, x => f(next(x)))
    case Update(status, next)    => Update(status, f(next))
  }
}
```

### Freeモナド

Freeモナド`Free`を次のように定義する。

```scala:Free.scala
case class Done[F[_]: Functor, A](a: A) extends Free[F, A]
case class More[F[_]: Functor, A](k: F[Free[F, A]]) extends Free[F, A]

class Free[F[_], A](implicit F: Functor[F]) {
  def flatMap[B](f: A => Free[F, B]): Free[F, B] = this match {
    case Done(a) => f(a)
    case More(k) => More[F, B](F.map(k)(_ flatMap f))
  }

  def map[B](f: A => B): Free[F, B] =
    flatMap(x => Done(f(x)))
}
```

そして、DSLを次のように修正する。

```scala
def fetch[A](screenName: String, f: WSResponse => Free[Twitter, A]): Free[Twitter, A] =
  More(Fetch(screenName, f))

def update(status: String): Free[Twitter, Unit] =
  More(Update(status, Done()))
```

そして、例えば“\_yyu\_”というユーザーの情報を取得して、取得できた場合はツイートするという処理を次のように書ける。

```scala
fetch(
  "_yyu_",
  res =>
    if (res.status == 200)
      update("exist")
    else
      update("not exist")
)
```

DSLの組み立てが完了したので、次はこれを実行する**インタープリター**を作成する。

### インタープリター

Freeモナドを使ったとしても、普通のインタープリターと特に違いはない。

```scala:TwitterInterpreter.scala
def runTwitter[A](dsl: Free[Twitter, A], env: UseWSClient with UseOAuthCred): Unit = dsl match {
  case Done(a) => ()
  case More(Fetch(screenName, f)) =>
    for {
      fws <- fetchUserByScreenName(screenName).run(env)
    } yield runTwitter(f(fws), env)
  case More(Update(status, next)) =>
    for {
      _ <- updateStatus(status).run(env)
    } yield runTwitter(next, env)
}
```

さきほど作ったDSLを次のように実行する。

```scala
val dsl = fetch(
  "_yyu_",
  res =>
    if (res.status == 200)
      update("exist")
    else
      update("not exist")
)

runTwitter(dsl, DefaultEnvironment.defaultEnvironment)
```

# まとめ

ReaderモナドとFreeモナドを使って依存を注入するDSLを作ることができたが、これには**Expression Problem**という解決しなければならない課題が残っている。次の機会にはExpression Problemの解決法として、**Inject**と**Tagless Final**の二つを紹介したい。

8/5 追記：
次回作を書きました。
→ [FreeモナドとTagless FinalによるDependency InjectionのためのDSL](http://qiita.com/yyu/items/377513f17fec536b562e)
