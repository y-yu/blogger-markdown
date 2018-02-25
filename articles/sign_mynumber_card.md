# はじめに

[マイナンバーカードでSSHする](https://www.osstech.co.jp/~hamano/posts/jpki-ssh)では、マイナンバーカードから公開鍵を取り出したり、マイナンバーカードの機能で認証するといった方法が紹介されている。この記事を参考に、マイナンバーカードの機能を使ってデータに署名をし、その署名をマイナンバーカードから取り出した公開鍵で検証するということを行った。

# 非接触式ICカードリーダの入手

今回の実験には用いた非接触式ICカードリーダは次の製品である。

- [ACR1251CL-NTTCom](http://www.ntt.com/business/services/application/authentication/jpki/download7.html)

この製品はOS XとWindowsのどちらにも対応しているとのことだが、今回はOS Xのみで実験をしている。後の操作は、この製品のドライバをインストールしてから行う。

# OpenSCのインストール

[マイナンバーカードでSSHする](https://www.osstech.co.jp/~hamano/posts/jpki-ssh)の著者であるhamanoさんにより、OpenSCの本体にマイナンバーカードへの対応がマージされたので、OS Xならばhomebrewからインストールして利用できる。ただし、まだreleaseには入っていないので、次のようなコマンドでリポジトリのHEADをインストールする必要がある。

```console
$ brew install opensc --HEAD
```

# 公開鍵の取得

マイナンバーカードから公開鍵を取得するには、カードリーダにマイナンバーカードを置き、次のコマンドを実行すればよい[^pem]。

```console
$ pkcs15-tool --read-public-key 1 > id_rsa.pub.pem
Using reader with a card: ACS ACR1251 CL Reader
```

[^pem]: OpenSSLのユーティリティで使いやすいように、ここではSSH形式ではなくPEM形式で出力する。

この`id_rsa.pub.pem`はたとえば次のようになる[^my]。

```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArvyj4+aPXatTrQ0kNu1k
MdZfEYnwUAYzrK4IjqQYAscf/PNEuC4bU6PcscmOhqaAQqXqegs6VbhCdYYgAHT3
4v4dXAZQDnOT1nBegnrRDywkK30xbD60bwIWqr6OFzks6kNXU+HmVo+PF3PQfWqL
pU9oYF3ddl79NjFAuaeR3sDoSG86kYcEqU5kWb3ByU7Bgi6irbj2fsw69geU+EEc
RFAOhmAXDEz1MHG0so7VWLFoGlGtd7oDnHGVm88wtGuAt0dZSVgEgpmYtP0izppr
4Eqmk66+iC4FcR0JRLs/mKfZAx+fJkQxCLgiojH/9HorkkpH80qTHW30z23PhTng
rQIDAQAB
-----END PUBLIC KEY-----
```

[^my]: これは著者のマイナンバーカードの公開鍵である。

# データに署名

マイナンバーカードにはデータに署名する機能（ハードウェア）が搭載されている。秘密鍵のようなセンシティブな情報をカードの外に持ち出すとコピーされてしまう恐れがあるため、カードがデータを受け取り署名されたデータを返すことで、秘密鍵をカードの外に出さないようにしている。
たとえば署名用に適当なデータの入ったファイルを次のように用意する。

```console
$ echo 'hello world!' > hello.txt
```

そして、このファイルのデータに対して次のコマンドで署名する。このコマンドを実行する時はカードリーダにマイナンバーカードを置く必要がある。

```console
$ pkcs15-crypt --pkcs1 -s -R -i hello.txt -o hello.sign
Using reader with a card: ACS ACR1251 CL Reader
Enter PIN [User Authentication PIN]:
```

キーボードからマイナンバーカードの登録時に設定したPINコードを入力して、それが正しければ署名されたデータ`hello.sign`が得られる。このファイルは次のようになっている。

```console
$ hexdump hello.sign
0000000 54 f2 66 d1 e4 41 33 85 93 e1 60 80 d4 78 02 b4
0000010 6f f0 a2 57 c8 80 d2 b6 24 9a ed f8 bc af a6 be
0000020 20 46 e2 28 d4 23 b9 ce 8f 81 93 ff 21 80 26 a7
0000030 a4 95 1e d3 ed 5a 3b 22 41 80 8e d9 a3 a1 84 7b
0000040 67 58 59 9d 00 3f 4c e0 00 24 ff 3f c1 d2 cb 42
0000050 60 4c a7 9a c4 bd e9 35 19 5b 05 83 03 a9 e3 64
0000060 7f 02 c0 37 91 32 0d d7 ae 30 72 fa 3f 4d 32 27
0000070 47 83 91 92 e5 44 7d 5f fe d8 ff e6 52 c8 2d fa
0000080 ab 5e ab 35 83 5d e2 30 b0 57 df d9 79 a8 22 f8
0000090 ad 35 ee 24 f9 25 4c 08 b8 22 fb cf 68 16 11 27
00000a0 7d 37 bb ad 7f c9 e3 6d 4d da 64 60 2a 78 72 36
00000b0 9d 05 bb 74 9e ba 0d 48 57 cb a7 e8 21 31 cb f9
00000c0 41 5a 8b 47 b2 ea c4 3b ea a1 a0 41 c7 78 40 44
00000d0 fe 84 5c 2f 5b f7 d5 f0 06 1a f1 1d 35 55 14 8d
00000e0 fa e9 ca 36 6f dc b6 5f 05 dc 1e 54 72 ff 70 a8
00000f0 8a 3f fb c5 09 22 42 94 70 df a6 76 f0 86 32 64
0000100
```

# 公開鍵による署名の検証

署名されたデータ`hello.sign`を公開鍵`id_rsa.pub.pem`で検証する。OpenSSLをインストールして、次のコマンドを入力すればよい。

```console
$ openssl rsautl -verify -in hello.sign -pubin -inkey id_rsa.pub.pem
hello world!
```

このように、署名と公開鍵から元のデータである`hello world!`を復元できた。

# まとめ

このように、マイナンバーカードによってデータに署名したり、その署名を公開鍵で検証するという実験を行った。マイナンバーカードを用いた認証が、SSHのログインや二段階認証などいろいろな用途へ応用されていくとよいと思う。
