# はじめに

最近Slack Bot作りに興味を持ち、どうせSlack Botを作るならば最も使い慣れた言語であるScalaで作りたくなった。また、[継続モナドを使ってWebアプリケーションのコントローラーを自由自在に組み立てる](https://qiita.com/pab_tech/items/fc3d160a96cecdead622)を読んで、継続モナドを利用することでSlack Botもより柔軟に作れるのではないかという考えのもと、Scalaを利用して作ってみた。この記事では、まずこのSlack Botの動かし方を説明し、すごく簡単にこのSlack Botでどのように処理を書くかについて述べる。

- https://github.com/y-yu/slackcont

## 発表資料

この内容について発表した資料が下記にある。

- [アニメーションあり版](https://y-yu.github.io/slackcont-slide/slackcont.pdf)
- [アニメーションなし版](https://y-yu.github.io/slackcont-slide/slackcont_without_animation.pdf)

<img width="70%" src="https://qiita-image-store.s3.amazonaws.com/0/10815/48cf8e0e-2fe3-e5d3-0e26-9c835b879aa5.png">

# 動かしてみる

次の手順で動かすことができる。

1. リポジトリをGitで持ってくる
2. `./src/main/resources/default.conf`をエディターで開く
3. 次の`token`のところにSlack Botのトークンを書き込む

    ```
    slack {
      token = "<Your Slack Bot Token>"
      duration = "5"
    }
    ```
    - `<Your Slack Bot Token>`を消して書き換える

4. Javaをインストールして`./sbt run Main`を実行する

# 中身の説明

## `SlackCont`

まず、`SlackCont`というデータ構造について説明する。これは次のように定義されている。

```scala:SlackCont.scala
case class SlackEnv(client: SlackClient, ec: ExecutionContext)

type SlackCont[A] = SlackEnv => ContT[Future, Unit, A]
```

これはSlackにメッセージを送信したりする`SlackClient`と、`Future`を操作するために利用する`ExecutionContext`の組である`SlackEnv`という型を引数にとって継続モナド`ContT`を返す関数のエイリアスである。関数にせず`ReaderT`でもいいかと思ったが、モナドが重なりすぎていて大変になると思い、このようにした。

このモナドを利用して、次のようなSlack Botをどう書けるのかを見てみる。

1. メッセージの内容が`Hello`かどうかを検査する
2. もしメッセージが`Hello`ならば書き込み中ステータスにする
3. 2秒間待機する
4. `World`という文字列を投稿する

## `HelloWorldCont`

もしメッセージが`Hello`に一致するならば継続に`World`を渡す処理は次のように書ける。

```scala:HelloWorldCont.scala
object HelloWorldCont {
  def apply(message: Message): SlackCont[String] = SlackCont[String] { env =>
    implicit val ec: ExecutionContext = env.ec

    k =>
      for {
        _ <- if (message.text == "Hello") {
          k("World")
        } else {
          Future.successful(())
        }
      } yield ()
  }
}
```

- https://github.com/y-yu/slackcont/blob/master/src/main/scala/com/github/yyu/slackcont/cont/impl/HelloWorldCont.scala

このように`Hello`でなかった場合は継続`k`を利用せず、そのまま成功を返して終了する。

## `TypingCont`

Slackでタイピング状態を送信する処理は次のように書ける。

```scala:TypingCont.scala
class TypingCont @Inject()(
  threadSleep: ThreadSleep
) {
  def apply(channelId: String, msec: Long): SlackCont[Unit] = SlackCont { env =>
    implicit val ec: ExecutionContext = env.ec

    k =>
      env.client.indicateTyping(channelId) // 失敗を無視する
      threadSleep.sleep(msec)
      k(())
  }
}
```

- https://github.com/y-yu/slackcont/blob/master/src/main/scala/com/github/yyu/slackcont/cont/impl/TypingCont.scala

まず、スリープする処理はテストのときに邪魔なのでGuiceでDIしている。そして、Slackクライアントにタイピングする命令を送り、その結果に関わらず継続を実行する。

## `SayCont`

引数に渡されたチャンネルに、メッセージを投稿する処理は次のように書ける。

```scala:SayCont.scala
object SayCont {
  def apply(sendChannelId: String, sendMessage: String): SlackCont[Long] = SlackCont[Long] { env =>
    implicit val ec: ExecutionContext = env.ec

    k =>
      for {
        n <- env.client.sendMessage(SlackSendMessage(sendChannelId, sendMessage))
        r <- k(n)
      } yield r
  }
}
```

- https://github.com/y-yu/slackcont/blob/master/src/main/scala/com/github/yyu/slackcont/cont/impl/SayCont.scala

この処理では`env.client.sendMessage`は`Future[Long]`を返すので、もし投稿に失敗して`Future.failed`となった場合には`Future`の`flatMap`が失敗し継続は実行されない。

## `Main`

それではこれらを組み合せて実際に動くようにしてみよう。

```scala:Main.scala
val injector = Guice.createInjector(new DefaultModule)

val slackRunner = injector.getInstance(classOf[SlackRunner])

val typingCont = injector.getInstance(classOf[TypingCont])

slackRunner.onMessage(msg =>
  for {
    world <- HelloWorldCont(msg)
    _ <- typingCont(msg.channel, 2000)
    _ <- SayCont(msg.channel, world)
  } yield ()
)
```

- https://github.com/y-yu/slackcont/blob/master/src/main/scala/com/github/yyu/slackcont/main/Main.scala

このように、比較的直感的に処理を組み合わせていくことができる。

# まとめ

このように継続モナドを組み合せてSlack Botを作ってみたが、まだ機能がそんなにないので継続を利用したおもしろい処理を書けていない。もしそういう機能を実装できたら、また追記したいと思う。

