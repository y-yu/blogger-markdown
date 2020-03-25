---
title: 量子コンピュータでイベントの開催を決める
tags: 量子コンピュータ IBMQ
author: yyu
slide: false
---
# はじめに

最近は新型コロナウィルスの影響で、イベントを開催するかどうかの判断が難しくなっています。この記事を書いている僕も、実は部署の送別会を企図していました。そこで[IBM Q](https://www.ibm.com/quantum-computing/learn/what-is-ibm-q/)という量子コンピュータとそれをクラウド上から実行できる[IBM Q Experience](https://quantum-computing.ibm.com/)を利用して、量子ビットが持つ確率的な性質を利用してイベントのやるやらを決定しようと思いました。量子ビットは誰かの都合や建前を忖度しません。

# 準備

IBMのアカウントを取得して、[IBM Q Experience](https://quantum-computing.ibm.com/)へ移動すると、量子コンピュータを利用したい理由などいくつかの質問に解答すると使えるようになります。今回は送別会のやるやらを決めるために使いたいので、そのように書いておきます。

<blockquote class="twitter-tweet" data-conversation="none"><p lang="en" dir="ltr">“I am planning to our division&#39;s farewell party but considering a new corona virus infection I want to use a qubit to determine if the party will be held or not.” <a href="https://t.co/WFMxzXDleY">pic.twitter.com/WFMxzXDleY</a></p>&mdash; 吉村 優 / YOSHIMURA Yuu (@_yyu_) <a href="https://twitter.com/_yyu_/status/1234473945404858370?ref_src=twsrc%5Etfw">March 2, 2020</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

$$
\def\bra#1{\mathinner{\left\langle{#1}\right|}}
\def\ket#1{\mathinner{\left|{#1}\right\rangle}}
\def\braket#1#2{\mathinner{\left\langle{#1}\middle|#2\right\rangle}}
$$

# 回路づくり

IBM Q Experienceの画面でどんどん回路を作っていきます。といっても今回は$\frac{1}{2}$で`true`か`false`みたいな1bitが得られればいいので、次のような簡単な回路となります。

![circuit.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/c1955fb2-efcf-4107-136e-bc40a28092de.png)

$\ket{0}$にアダマールゲート（$H$）をかけてからZ軸測定しているだけの超シンプルな回路となりました。

# エミュレーター実行

まずはこれをシミュレーターで実行してみます。回路を保存したら、画面上の`RUN`ボタンを押すと次のようにどういうバックエンドで実行するか？を選択する画面があらわれます。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/00beaac2-5fc0-d06d-8930-dcd24988cfed.png" width="60%"/>

このようにまずはシミュレーターにしておいて、実行回数はとりあえず`1024`にしておきます。

![nijef25p.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/72577611-d067-1b78-b480-d001750c3ae7.png)

こういう感じで結果が出ました。`0`と`1`がほぼ50:50で出ているので成功のようです。

# IBM Qで実行

いよいよ実機でやっていきます。同じ回路をIBM Qの`ibmq_16_melbourne`という実機に投入してみます。偏りがないか見たいので、1024回実行します。

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/456eb0d5-3ad2-025d-c383-7b757933802e.png" width="60%"/>

![riw7hxivl.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/2efde047-1297-cfa6-c8e1-ff841cd23da1.png)

偏ってますね……。`00000`と表示されていることからも、測定ができる量子ビットは5個ありそうなので、片っ端からやっていって一番50:50に近いやつを使うことにするべきなんでしょうか……。とりあえずもう1回実行したところ、もうちょっと50:50に近付きました。

![1ihyyrau.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/10815/317667f5-00a8-6792-14c6-a0739fac30db.png)

まあ多少はヨシ！ということでこのまま最下位ビットを使う方針でいきます。

# 判定プロトコル

まああとは簡単に次のようにすればいいと思います。

1. Slackなどで「1ならやる、0ならやらない」といった1bitとやる・やらを対応させたものを公開する
2. 上記の量子回路をIBM Qで実行する
3. （2）の結果を（1）の対応と照合してやるやらを判定する

# まとめ

こういった状況であると、なんでも中止にしておいた方がいいのかな？という気分になります。個々の判断は尊重されるべきですが、信念を持った判断をしたいとも思います。量子コンピュータに判断を委ねるというのも、運まかせですが運にまかせるという1つの信念かもしれません。
また僕の企図していた送別会のやるやらは、決まり次第ここに追記します。

## 追記 3/25

**中止になってしまいましたー :innocent:**

