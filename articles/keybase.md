# はじめに

最近、TwitterやGitHubなどと連携できる公開鍵基盤**[Keybase](https://keybase.io/)**に招待していただいたので、このKeybaseがどのようなサービスであるのかを、前提となる**公開鍵暗号**や**公開鍵基盤**などから順を追いつつ軽く紹介していきたいと思います。

![スクリーンショット 2015-09-20 23.28.50.png](https://qiita-image-store.s3.amazonaws.com/0/10815/08c6854f-516c-c69e-7e36-57654d98f667.png)

# 共通鍵暗号と公開鍵暗号

暗号にはおおまかに二種類があり、共通鍵暗号（対称鍵暗号）と公開鍵暗号です。これらの特徴を次のようになっています。

## 共通鍵暗号

共通鍵暗号は[DES](https://ja.wikipedia.org/wiki/Data_Encryption_Standard)や[AES](https://ja.wikipedia.org/wiki/Advanced_Encryption_Standard)が有名で、次のような特徴を持ちます。

- 同じ鍵（秘密鍵）を使って暗号化と復号化[^decrypt]を行う
- 後述する公開鍵暗号に比べて一般に高速である
- あらかじめ、暗号通信を行う際に秘密鍵を安全な方法で共有する必要がある

[^decrypt]: この記事では“decrypt”を「復号化」と訳すことにしますが、日本語としては「復号」が正しいという主張もあるようです。この記事では[暗号技術入門 第3版 秘密の国のアリス](http://www.amazon.co.jp/dp/4797382228)や[暗号と確率的アルゴリズム入門―数学理論と応用](http://www.amazon.co.jp/dp/4431710256)で採用されている「復号化」という言葉を使いますが、個人としてはどちらでもよいと思います。

## 公開鍵暗号

公開鍵暗号は[RSA](https://ja.wikipedia.org/wiki/RSA%E6%9A%97%E5%8F%B7)が有名で暗号化に用いる**公開鍵**と復号化に用いる**秘密鍵**の二つの鍵を使うのが特徴です。

- 復号化に専用の鍵を使うので、秘密鍵を安全な方法で共有する必要がない
- 共通鍵暗号に比べて、一般に低速である
- 署名に使うこともできる

# 公開鍵基盤（PKI）と中間者攻撃

さて、公開鍵暗号のおかげで共通鍵暗号のように鍵を安全な方法で事前に共有する必要はなくなりましたが、次のような課題が生まれました。

- ある公開鍵が、本当に通信相手の公開鍵であることを保証できない

これができないと、**中間者攻撃**ができてしまいます。

## 中間者攻撃

中間者攻撃とは、ある人物**アリス**と**ボブ**が通信を行っているとして、この通信を傍受・改竄できる攻撃者**マロリー**が二人の中間に割り込んで次のような攻撃をします。

1. アリスはボブに公開鍵**A**を送信する
2. マロリーは公開鍵**A**をマロリーの公開鍵**B**へ改竄する
3. ボブは公開鍵**B**を受信する（ボブはアリスの公開鍵と考えている）
4. ボブは公開鍵**B**を使って、メッセージ**M**を暗号化した結果**E**をアリスへ送信する
5. マロリーはマロリーの鍵で暗号化された**E**を復号化して**M**を取り出し、改竄した結果**M'**を生成し、それをアリスの秘密鍵**A**で暗号化してアリスへ送信する
6. アリスは送信された暗号文を復号化して、メッセージ**M'**を受信する

このように、ボブは公開鍵**B**が本当にアリスのものである、ということを判断できないと、このようにしてマロリーに情報を傍受されたり改竄されたりしてしまいます。中間者攻撃を防ぐひとつの作戦として、[公開鍵基盤](https://ja.wikipedia.org/wiki/%E5%85%AC%E9%96%8B%E9%8D%B5%E5%9F%BA%E7%9B%A4)があります。公開鍵基盤があれば、ボブは受信した公開鍵**B**が本当にアリスの鍵であるのかを問い合せて、公開鍵**B**が第三者の鍵であると気がつきます。

# SNSとの連携

Keybaseも公開鍵基盤の一つなのですが、これはTwitterやGitHubなどといったSNSのアカウントと公開鍵を紐付けます。このようにすることで、例えばあるTwitterアカウントを持つ人間と公開鍵暗号によるメッセージの交換を行いたいときに、あるTwitterアカウントと公開鍵を紐付ける公開鍵基盤になります。

https://keybase.io/yyu

![スクリーンショット 2015-09-21 0.01.09.png](https://qiita-image-store.s3.amazonaws.com/0/10815/41fcaec9-8b7a-4160-9581-840a1250a937.png)

このKeybaseですが、紐付けの仕方におもしろさを感じましたので、次のSNSアカウントの紐付けについて紹介したいと思います。

- Twitter
- GitHub
- ドメイン

また、Keybaseは現在（2015年9月）この他にも次のようなSNSに対応しています。

- reddit
- coinbase.com
- hacker news
- 自分のウェブサイト
- bitcoin address

## Twitterとの連携

このようなツイートを行うことで連携します。

<blockquote class="twitter-tweet" lang="ja"><p lang="in" dir="ltr">Verifying myself: I am yyu on Keybase.io. lGcJIJfXwJ12AJpyOIQbfUIz3_xpzTUJSSOS / <a href="https://t.co/B8mVeDB817">https://t.co/B8mVeDB817</a></p>&mdash; 吉村 優 (@_yyu_) <a href="https://twitter.com/_yyu_/status/645582793032929280">2015, 9月 20</a></blockquote>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

## GitHubとの連携

次のような投稿を[Gist](https://gist.github.com/)に行います。

https://gist.github.com/yoshimuraYuu/661475c532e721f1d790

> ### Keybase proof
> 
> I hereby claim:
> 
>   * I am yoshimuraYuu on github.
>   * I am yyu (https://keybase.io/yyu) on keybase.
>   * I have a public key whose fingerprint is F299 3A15 492A 691B C4EE  1919 3730 168B 63BE ABA3
> 
> To claim this, I am signing this object:
> 
> ```json
> {
>     "body": {
>         "key": {
>             "eldest_kid": "0101514b12352d78ca91fcc55e5943d4a82f388d89ba10f8a8c04c67d529529301b40a",
>             "fingerprint": "f2993a15492a691bc4ee19193730168b63beaba3",
>             "host": "keybase.io",
>             "key_id": "3730168b63beaba3",
>             "kid": "0101514b12352d78ca91fcc55e5943d4a82f388d89ba10f8a8c04c67d529529301b40a",
>             "uid": "a5abc00759ab7935959fe9c9e7c06119",
>             "username": "yyu"
>         },
>         "service": {
>             "name": "github",
>             "username": "yoshimuraYuu"
>         },
>         "type": "web_service_binding",
>         "version": 1
>     },
>     "ctime": 1442470224,
>     "expire_in": 157680000,
>     "prev": "1c9cac05eb3ce4d6435b9aeca57e2416c5ebfe93ff555f418932f1cd0a8b4e1c",
>     "seqno": 2,
>     "tag": "signature"
> }
> ```
> 
> with the key [F299 3A15 492A 691B C4EE  1919 3730 168B 63BE ABA3](https://keybase.io/yyu), yielding the signature:
> 
> ```
> -----BEGIN PGP MESSAGE-----
> Version: Keybase OpenPGP v2.0.46
> Comment: https://keybase.io/crypto
> 
> yMIlAnicrVJ7SBRBHD4ze2hlamSQQW2ZPa7a2d253bkCqRDKgiSwssJrZnb2XC/3
> rr0787AHFUIvjigkMBLsIUWCkVIESQ/CyEdWRBi9zLKIAiPKR9Bj7qh/oj8bBob5
> ft/38f1+/G6PT3QkJ7T8GOgennrdm9B+Mxp2FH4rKqgUiF+PCO5KwcfiD9uqs2DI
> 4zN1wS2IQAQQKARIMpR0VaMYAYNSCBlEiqwrWJMMWdN0DREMREPDGhUV6lJ1KCF+
> ZREQRcSCUzBMy8vsgG1aIW5rSAjJGEAFSdiFAKEKYwABJKtc4dKISyYMEyxzYYk/
> GFPwcAQH2ULTzzH+8cTj/YP/n3OH43YYYkJFUYUIExXJEEFkMEQRU6noAgDFiEFm
> W7iMcXYkEhZ2OgUOlJuUxWb6u+A1QyVh8hfZHywxy8I2LgrHVaFIIAZvZ8Tz28BD
> TEvn4+O6cmYHTb8luAFn0pAZcwCKIimqKEmKU2AVAdNmHjPGgKpLE/lxCgGblXNL
> QBHFVISMyJQpukuRIUGYUQxVJinARXmFdyUbBoTQUICGZMkAVBexRhQGqBBraZvl
> F9wSj4m93DJoei0cCttM2HnrxuaRjoRkx6ikEbG1ciSPnfhn2cZao3/i1orE9y+G
> iq5mXFo669SHfTdWjkhbV3dwzbzeqk70pDW/rm3/gS1Dr2cevpM7+fCVUrv6bWHz
> ofMdn/MySyL6iqyu5fK+OZmZzdv6GjsXfc3v6Ug/vTi7OzhtTC1KtXIed5x40FuY
> tCky/cuRC08a1vpy0htp1xl18OKM+Zt7mn4OvHrxJffeEnNuza6c1b43T3eUT0/b
> vYHsKUjJ2tvSULrAzNxlR7t3N7RUFVe3r6rvmfTs2ez20sHw2dMn+hey41OeH73y
> stb80eLJo13OC+u/1z2sXf2ub8LGmujJ6LVP+UnnPt7KaHqUcn/G5dQlbcPZDwZH
> 9j/PSMv/eHdZvbP+ZVPqseJxvwBI10Ww
> =bv/e
> -----END PGP MESSAGE-----
> 
> ```
> 
> And finally, I am proving ownership of the github account by posting this as a gist.
> 
> ### My publicly-auditable identity:
> 
> https://keybase.io/yyu
> 
> ### From the command line:
> 
> Consider the [keybase command line program](https://keybase.io/docs/command_line).
> 
> ```bash
> # look me up
> keybase id yyu
> 
> # encrypt a message to me
> keybase encrypt yyu -m 'a secret message...'
> 
> # ...and more...
> ```

## ドメインとの連携

ドメインの設定で次のようなレコードを追加します。

```
txt @ keybase-site-verification=2XGrnKYkYX33RHB6Pk-Qm3OmJGQcjGncCgL1SyrfBtU`
```

![スクリーンショット 2015-09-20 23.48.47.png](https://qiita-image-store.s3.amazonaws.com/0/10815/8504e5ff-52f9-b1f0-661d-1cbd09bbe919.png)

# 暗号通信を行ってみる

実験として、僕が僕に対してメッセージを送ってみたいと思います。

https://keybase.io/encrypt

宛先を自分にして、送りたいメッセージを投入します。

![スクリーンショット 2015-09-21 0.04.15.png](https://qiita-image-store.s3.amazonaws.com/0/10815/3a8558a0-8d77-04a9-7594-44b041fa0fc5.png)

そして“Encrypt”ボタンを押せば、暗号文が生成されます。

![スクリーンショット 2015-09-21 0.05.51.png](https://qiita-image-store.s3.amazonaws.com/0/10815/ee190b5f-19c3-e799-3076-0acd8163b268.png)

出力された暗号文はこちらになります。

```
-----BEGIN PGP MESSAGE-----
Version: Keybase OpenPGP v2.0.46
Comment: https://keybase.io/crypto

wcBMAyKXuIIaCumXAQf+NtQq00U0dUz2UkuPcHSGQdm/cvSwHho3E24GWiZkWspF
4jmBMiCxGcpLM3Ovtn9fDaqIoKnXlMeF9bzpDJzL5bS81d52s2mcEWfdftUnESSE
uy9+XkKmV4uEsCx5I2+vGmoQUYQR3s2pLgQfwKB66sJE50fq7DD+AXrP2gkOEuV2
++UeRXkeaVstnFAlcQD6Vw63hIJKp4K7JEBdkzO7/BtEsrYfZbybIXVInUwKSlbb
uCFXqlxCRbhkD2Faduml5GWe7IP2Vs2dHiKJ/hS/msk7iJL4dmuz4nG+V0SdYlB5
uHpIqm0W5y0XSiz4ASAKRNypFsdYwNv+lU8NK26GR9JUAWzK8c9COZBbIUeW5lQH
ssBg5CypeK3xFa2NSQ4SGlPDKQNfQfv6+ECcRdcxC9FBN2WVvGO40svemKtKHkq6
FWMkEPDEpbOVsLQBSiNV2TPOaDft
=TQmj
-----END PGP MESSAGE-----
```

これをログインして、復号化してみます。メッセージとKeybaseのパスワードを入力して復号化します。

https://keybase.io/decrypt

![スクリーンショット 2015-09-21 0.08.23.png](https://qiita-image-store.s3.amazonaws.com/0/10815/5e02f618-8cce-1e28-26ce-2869be00d72a.png)

暗号化と同じように“Decrypt”ボタンを押せば復号化が完了します。

![スクリーンショット 2015-09-21 0.10.09.png](https://qiita-image-store.s3.amazonaws.com/0/10815/af61326c-f5f3-d0c0-5618-5b7359194bd2.png)

きちんと元のメッセージが復号化されています。

# まとめ

KeybaseはSNSと連携した公開鍵基盤です。今回は紹介しませんでしたが、Keybaseを使っている人の間で**署名**をすることもできるので、メッセージを本当にその人が発信したのかが重要な局面で活躍する可能性もあります。
Keybaseは現在、招待制でメンバーを募集しているので、興味のある方は知っている人をKeybaseで検索して招待してもらうとよいと思います。
