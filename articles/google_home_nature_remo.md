# はじめに

[Google Home mini](https://store.google.com/product/google_home_mini)を購入したので、前から持っていた[Nature Remo mini](https://nature.global/jp/top)と連携して、部屋の温度を教えてくれる機能を実装した。このような記事はすでにいくつかネット上に存在するが、次の点が気になったので改めて書くことにした。

- 情報が古くなって後述する[Dialogflow](https://dialogflow.com/)の使い方が変っている
- ローカルネットワーク内にサーバーを構築する必要がある
    - Google HomeもNature Remoもインターネットからアクセス可能なAPIがあるため、実はローカルサーバーは不要である
- Dockerで[Heroku](https://www.heroku.com)にデプロイできる仕組みがない

このためこの記事ではこれらが解決されて次のようになることを目指した。

- 執筆時点でのUIをキャプチャした（Dialogflowは所見ではごちゃごちゃしているので、解説とUIが違うと手間がかかる）
- サーバーアプリケーションはDockerで起動できるようにし、Herokuにデプロイすることで動作する
    - サーバーアプリケーションはPython + [Flask](http://flask.pocoo.org/)で実装した

この記事で作ったプログラムは下記に置かれている。

- https://github.com/y-yu/google-home-nature-remo-temperature

この記事を読んで何か分かりにくいことや改善点を見つけた場合、気軽にコメントなどで教えてほしい。

## 追記（2019/10/12）

公式で温度を教えてもらう機能が実装されました:tada: したがってこの記事の方法を使わなくても温度をスマートスピーカーから教えてもらえます。

- [スマートスピーカーに部屋の室温を教えてもらおう！
](https://nature.global/jp/blog/2019/10/10/ask-google-temp)

# 準備

## Nature Remoのアクセストークンの取得

https://home.nature.global/home へアクセスして`Generate access token`を押せば発行される。

<img width="80%" alt="accesstoken.png" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/3bdc92a4-d9e2-4c80-c3b9-31d3a6ea76be.png">

## Herokuのアプリケーションを作成

https://dashboard.heroku.com/apps へアクセスして`New > Create new app`を押せばよい。

<img width="30%" alt="" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/33a98912-40b6-b7f6-d595-7c0608ecd952.png">

そして`App name`は`google-home-nature-remo`としたが、この命名はすでに筆者が利用してしまったので別の名称にしなければならない。この`App name`は後にコマンドライン上やURL上で利用するので、別の名前にした場合はこの記事のいろいろな部分を適宜修正する必要がある。この命名がコマンドラインやURLで必要になった場合は、`《App name》`と表記する。

<img width="70%" alt="" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/595b7cca-197f-835e-a7c7-e36582b14126.png">

最後に`Create app`を押す。これでアプリケーションがデプロイできるようになる。そしてアプリケーションのために環境変数を設定する。[https://dashboard.heroku.com/apps/《App name》/settings]()へアクセスし次のように環境変数を入れる。

<img width="80%" alt="env.png" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/cfd0c272-0b8e-4d2f-90b9-1ca94d410702.jpeg">

`NATURE_REMO_TOKEN`は先ほど発行したNature Remoのアクセストークンであり`BASIC_AUTH_USERNAME`と`BASIC_AUTH_PASSWORD`はそれぞれGoogle Home（正確にはDialogflow）がこのHerokuアプリケーションにアクセスするためのBasic認証の情報である。これはURLが特定されると部屋の温度を取得される恐れがあるため、このように認証をかけておくことにする。

# サーバーアプリケーションのデプロイ

HerokuのDockerアプリケーションをデプロイする。次のような流れを行う。

1. `git clone https://github.com/y-yu/google-home-nature-remo-temperature.git`
2. `cd google-home-nature-remo-temperature`
3. `heroku login`
    * もしCLIの`heroku`がない場合はHomebrewなどで適宜インストールする
4. `heroku container:login`
5. `heroku container:push web -a 《App name》`
6. `heroku container:release web -a 《App name》`

これでサーバーサイド側は完成のはずである。次のコマンドでテストするとよい。

```console
$ curl -XPOST --basic -u "user:*******" https://google-home-nature-remo.herokuapp.com/temperature | jq
{
  "payload": {
    "google": {
      "expectUserResponse": false,
      "richResponse": {
        "items": [
          {
            "simpleResponse": {
              "textToSpeech": "現在の室温は24.39度です"
            }
          }
        ]
      }
    }
  }
}
```

このようなJSONが表示されれば成功である。

# Google Assistantアプリケーションの作成

https://console.actions.google.com/ へアクセスし`New project`を押すと、次のような画面があらわれる。

<img width="60%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/845c176c-563f-8f0d-d0b7-d8e38d0bf015.png">

言語を日本語、地域を日本にして`Create project`する。するとWelcomeページが表示される。

<img width="60%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/1899f5ca-7b8a-e7ac-cda6-eaba413259db.png">

ここからGoogle Homeで呼びだすための設定をしていくので、上のタブの`Develop`を押す。

## Invocationの設定

左のタブに`Invocation`というのがあるので、まずはこれを設定する。これは「OK, Google. `○○○○○`につないで」の`○○○○○`を決めることで、さきほど作ったアプリケーションを呼び出すことができるようになる。ここでは`部屋の温度`にした。

<img width="60%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/1cfe31b1-26c8-aaf5-5bbd-e913a27284df.png">

これで「OK, Google. 部屋の温度につないで」と言うとこのGoogle Assistantアプリケーションが起動するようになる。

## Actionの追加

それではDialogflowを使ってどのようなときにどうするのかを定義していく。あらかじめゴールを述べておくと「このアプリケーションが起動した時に、さきほど作ったHerokuアプリケーションに問い合わせてその情報を発言する」というものである。
まずは左側のタブから`Action`を選び、`Add action`を押す。

<img width="60%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/c7bf7b07-16b4-d5c1-f01d-da2cbadd3c68.png">

今回はbuilt-inではないので、Custom intentを作るため、画像のような`BUILD`ボタンを押してDialogflowへ移動する。

## Dialogflowの設定

次からは`Create new agent`で新しい設定を作成し、適当な名前をつける。ここからDialogflowを設定していく。

### Default Welcome Intentの無効化

このアプリケーションはデフォルトで「OK, Google. `○○○○○`につないで」の後にやることであるWelcome Intentが決っているが、今回このGoogle Assistantアプリケーションは温度を返す機能しかないため、このデフォルト機能は必要ない。

<img width="50%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/4422006b-3d0e-6772-7146-e8a585580ffa.png">

そこで上の画像のように`Events`に設定してあった`Welcome`を削除して空にしておく。

### Fulfillmentの設定

次にHerokuアプリケーションへ問い合わせる部分を定義する。左側のタブから`Fulfillment`を選び、`Webhook`を`ENABLE`にする。そしてHeroku側の環境変数に従ってBasic認証の情報とアプリケーションのURLを入力する。

<img width="80%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/dead290c-772d-24ad-682c-e3ccb416b1a1.png">

そして画面右下の`SAVE`を押す。

### Intentの設定

Dialogflowの左側のタプから`Intent`を押し、右上にある`CREATE INTENT`を押す。`Intent name`は適当に入れておけばよい。ここはユーザーのどういうアクションに対して何をするかを定義する部分であり、今回は機能が1つ（部屋の温度を返すだけ）なので、起動した瞬間にHerokuアプリケーションへ問い合わせてもらえばよい。
したがって、まずは`Event`を設定する。

<img width="50%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/d7012c85-4cb1-ebdf-90eb-f54b7605a1f5.png">

このように`Welcome`を設定した。そして一番下にある`Enable webhook call for this intent`を有効にすればHerokuアプリケーションへの問い合わせが行われる。

### Integrationsの設定

最後に追加したIntentをGoogle Homeで使う設定を書いておく。もう`Default Welcome Intent`はいらないので削除し、いま作った`room temperature`を入れる。

<img width="60%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/6aee44a2-5f93-69c2-e23f-651f3c526951.png">

また`Auto-preview changes`を入れておけば修正したときに、明示的な操作なく変更が適用されて便利である。ここで`TEST`ボタンを押してシミュレーターでテストしてみる。

<img width="60%" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/288fc301-9775-bcd1-df12-a9080f7292de.png">

このようになれば成功である。この時点でもう部屋のGoogle Homeから利用できる状態にあるので、たとえばこの例では「OK, Google. 部屋の温度につないで」と言えばきちんと応答される。

# おわりに

Google Homeアプリケーションの開発は、とにかく覚えることが多くて大変であった。この資料が他の方々の開発に役立てばよいと思う。

# 参考文献

- [Google HomeとFlask(Python)サーバでスマートスピーカーアプリを作成してみた](http://totech.hateblo.jp/entry/2018/02/06/162102)
- [Dialogflow API V2使ってGoogle Homeのアプリを作成](https://qiita.com/iton/items/356130e6697d18b27c1f)
- [Google Home + Nature Remo API で室温を喋らせる](https://blog.yuu26.com/entry/20180523/1527086494)
- [Google Home でハローワールド](https://dev.classmethod.jp/voice-assistant/actions-on-google/hello-world-on-google-home/)
- [Nature Remoの公式APIの使い方](https://qiita.com/sohsatoh/items/b710ab3fa05e77ab2b0a)


