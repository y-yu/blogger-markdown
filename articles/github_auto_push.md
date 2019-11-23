---
title: Travis CI（bionic）でGitHubに公開鍵認証でプッシュする
tags: TravisCI GitHub openssl
author: yyu
slide: false
---
# はじめに

[Travis-CI でコミットして GitHub にプッシュする - 公開鍵認証を利用してみる](https://blog.eiel.info/blog/2014/02/18/github-push-from-travis/)は大変すばらしい記事であり、これを利用して筆者も長くTravis CIで自動生成したPDFを`gh-pages`ブランチへプッシュするといったスクリプトを運用してきた。ところが筆者がTravis CIのLinuxディストリビューションをUbuntu 18.04 LTS（bionic）へアップデートしたところ、この方法が動かなくなってしまった。これは18.04からOpenSSLのバージョンが1.1系となり、オプションが変ってしまったからである。
この記事では、OpenSSL 1.1系で利用できるように元記事の内容を（雑に）翻訳する。

# OpenSSL 1.1系のインストール

macOSを利用している場合は次のコマンドで入手できる。

```console
$ brew install openssl@1.1
```

環境変数`PATH`を次のように設定する。

```console
$ echo 'export PATH="/usr/local/opt/openssl/bin:$PATH"' >> ~/.zshrc
```

このような結果が得られれば成功である。

```console
$ openssl version
OpenSSL 1.1.1d  10 Sep 2019
```

# 秘密鍵の暗号化

次のような手順で行う。

1. 秘密鍵の生成

    ```console
$ ssh-keygen -f deploy_key
    ```
2. 秘密鍵を暗号化用のパスワード[^pass]を生成

    ```console
$ password=`cat /dev/urandom | head -c 10000 | openssl sha1 | cut -d' ' -f 2`
    ```
    - ここも`openssl sha1`の挙動が変っているため若干のコマンド修正が必要であることに注意せよ
3. 秘密鍵の暗号化

    ```console
$ openssl aes-256-cbc -pass "pass:$password" -pbkdf2 -in deploy_key -out deploy_key.enc -a
    ```
    - まず`-k`オプションではなく`-pass`オプションとした。これは`pbkdf2`というのがパスワードベース暗号化（PBE）であり、ストレッチングやソルト付与などいろいろなことをやったうえで共通鍵を内部で生成して暗号化する
    - ストレッチング回数などは規格があり、今回は`pbkdf2`を採用した


[^pass]: 元記事では文章において共通鍵としているが環境変数名は`password`であり、パスワードと共通鍵を区別してはいないと思われる。この記事ではパスワードを元に共通鍵を作成する方法を新たに採用するため、利用者は意識する必要はないが一応この2つの言葉を区別して利用する。

このようにして、あとは元記事にあるようにGitに追加したりGitHubに設定すればよい。

# 暗号化された秘密鍵の復号

次のコマンドを利用すればよい。

```console
$ openssl aes-256-cbc -pass "pass:$secret" -pbkdf2 -in .travis/deploy_key.enc -d -a -out deploy.key
```

# まとめ

このようにすることでOpenSSL 1.1系でも利用できる。

