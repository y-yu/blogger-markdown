# はじめに

[CSS2016](http://www.iwsec.org/css/2016/index.html)において、橋本さんらにより「カードを用いた秘匿グループ分けプロトコル」という論文が発表された。この論文では番号が書かれたカードを用いて、メンバーをいくつかのグループに分ける方法を提案し、さらにあるグループにおいては他のメンバーが誰か分からないが、あるグループにおいては他のメンバーが誰であるのかが分かる、というプロトコルを構成した。この記事ではこの論文で発表された内容をカードではなくコンピューター上で実行する方法について述べる。
この記事のPoCは次の場所に置かれている。

https://gist.github.com/y-yu/e8b9d2a83c71f000646dc4ce58f0efb1

この記事を読んで、なにか分からないことや改善するべき点を見つけた場合は気軽にコメントなどで教えて欲しい。

# カードを用いた秘匿グループ分けプロトコル

まず、橋本さんらが提案したカードを用いたプロトコルについて述べる。

## ナンバーカード

このプロトコルでは**ナンバーカード**と呼ばれる次のように番号が印刷されたカードを用いる。

```math
\def\card#1{\boxed{\vphantom{1}#1\,}}

\card{1}\,\card{2}\,\card{3}\,\card{4} \cdots \card{n}
```

これらのカードはいずれも裏が$\card{?}$となっており、区別することができない。

## Pile-Scramble Shuffle

次に、**Pile-Scramble Shuffle**について述べる。これはカード列の全ての置換を一様な確率で適用する操作である。

```math
\def\pss{\left\lvert\Big\lvert \card{?} \middle\vert \card{?} \middle\vert \cdots \middle\vert \card{?} \Big\rvert\right\rvert}

\pss\, (x) \rightarrow \card{?}\, \card{?} \cdots \card{?}\, (rx)
```

## 置換のランダマイズ

次の方法である置換$\tau$と同じ型[^type]に属する置換$\rho$をランダムに選ぶ操作を定義する。

[^type]: 置換$\tau$を互いに素な巡回置換の積として表わした時、$i = 1, 2, \dots, k$に対して長さが$r_i$の巡回置換がちょうど$m_i$個現れるならば、$\tau$は型$\left< r_1^{m_1}, r_2^{m_2}, \dots, r_k^{m_k}\right >$を持つ。

```math
\def\twopair#1#2{%
  \begin{matrix}
      #1 \\
      #2
  \end{matrix}
}
\def\twocards#1#2{\twopair{\card{#1}}{\card{#2}}}
\def\twopss#1#2{\left\lvert\left\lvert \twocards{?}{?} \middle\vert \twocards{?}{?} \middle\vert \cdots \middle\vert \twocards{?}{?} \right\rvert\right\rvert \twopair{(#1)}{(#2)}}
```

1. 順番に並んだカード列を2つ用意し、裏にする

    ```math
    \card{1}\,\card{2} \cdots \card{n} \rightarrow \card{?}\,\card{?} \cdots \card{?} \\
    \card{1}\,\card{2} \cdots \card{n} \rightarrow \card{?}\,\card{?} \cdots \card{?}
    ```
2. 2つをまとめてPile-Scramble Shuffleを適用する

    ```math
    \twopss{id}{id} \rightarrow \twocards{?}{?}\, \twocards{?}{?} \cdots \twocards{?}{?} \twopair{(\sigma)}{(\sigma)}
    ```
3. 下のカード列に$\tau$を適用する

    ```math
    \twocards{?}{?}\, \twocards{?}{?} \cdots \twocards{?}{?} \twopair{(\sigma)}{(\sigma)} \rightarrow \twocards{?}{?}\, \twocards{?}{?} \cdots \twocards{?}{?} \twopair{(\sigma)}{(\tau\sigma)}
    ```
4. 2つをまとめてPile-Scramble Shuffleを適用する

    ```math
    \twopss{\sigma}{\sigma} \rightarrow \twocards{?}{?}\, \twocards{?}{?} \cdots \twocards{?}{?} \twopair{(r\sigma)}{(r\tau\sigma)}
    ```
5. 2つのカード列のうち上のカード列を開示して、上のカード列が順番に並ぶように上下のカードペアを並び換える。これにより、下の行は$(r\sigma)^{-1} = \sigma^{-1}r^{-1}$の並び換えを適用される。よって、$\sigma^{-1}r^{-1}r\tau\sigma = \sigma^{-1}\tau\sigma$というカード列が得られる

    ```math
    \twocards{a}{?}\, \twocards{b}{?} \cdots \twocards{c}{?} \twopair{r\sigma}{(r\sigma)} \rightarrow \twocards{1}{?}\, \twocards{2}{?} \cdots \twocards{n}{?} \twopair{id}{(\sigma^{-1}r^{-1}r\tau\sigma)} = \twocards{1}{?}\, \twocards{2}{?} \cdots \twocards{n}{?} \twopair{id}{(\sigma^{-1}\tau\sigma)} 
    ```
6. 生成した次のカード列$\sigma^{-1}\tau\sigma$を$\rho$とする

    ```math
    \card{?}\, \card{?} \cdots \card{?}\, (\sigma^{-1}\tau\sigma)
    ```

## 秘密グループ分けプロトコル

まずプレイヤーが$n$人おり、これを$m$個のグループ$A_1, A_2, \dots, A_m$にグループ分けすることを考える。また、人数が$r_i$人のグループが$m_i$個あるとすると、$n = \sum_{i=1}^{k}m_ir_i$であり$m = \sum_{i=1}^{k}m_i$である。なお用意するカードはメンバーを表す$1$から$n$までのカードと、所属を表す$n + 1$から$n + m$までのカードの合計$n + m$枚である。

1. $\left< (r_1 + 1)^{m_1}, (r_2 + 1)^{m_2}, \dots, (r_k + 1)^{m_k}\right >$の型である置換に属する任意の$\tau$を選ぶ。ただし、この$\tau$を巡回置換の積で表したとき、その各々の因子には所属を表すナンバーを含んだサイクルにする
2. $r = \text{max}(r_1, \dots, r_k)$として、ランダマイズに用いる$\sigma$を$2r$個まとめて作成する。ただし$\sigma$をつくるときは$1$枚目から$n$枚目のカードについてのみPile-Scramble Shuffleを適用する
3. (2)の$\sigma$を用いて$\rho$を作成する。同じ$\sigma$を用いて$\tau^2$から$\rho^2$を作成できるので、同様に$\rho, \dots, \rho^r$を作成する
4. プレイヤー$i$はカード列$\rho, \rho^2, \dots, \rho^r$の左から$i$番目をそれぞれ一枚ずつドローする。各プレイヤーは所属を表すカードを一枚と、同じグループのメンバー全員のカードを一枚ずつ得る

# Mental Pokerを用いた秘密グループ分けプロトコル

## Metal Pokerとは

Mental Pokerとは信頼できる第三者なしでポーカーを実行するためのプロトコルである。詳細なプロトコルについては下記を参照して欲しい。

http://qiita.com/yyu/items/8d8c82ba729b06b26e67

このプロトコルでは次の操作を提供する。

- 公平なカードのシャッフル
- 公平なカードのドロー
- 公平なカードの公開

## プロトコル

これを用いて次のように秘密グループ分けプロトコルを実装する。ただし、適宜ゼロ知識証明を用いて不正をチェックする必要がある。

1. Mental Pokerのセットアップを行う
2. $1, 2, \dots, n$のカードを2組用意しシャッフルし$c := (c_1, c_2)$とする（このときのシャッフルの置換を$\sigma_1$とする）
3. $n + 1, n + 2, \dots, n + m$のカードを2組用意し暗号化したものを$d := (d_1, d_2)$とする
4. 任意のプレイヤーが$\tau$を選び、条件に適合することを他の全てのプレイヤーが検証する
5. $c$と$d$を結合してこの並びを$\sigma$とし、2組のうちの片方に$\tau$を適用してシャッフルする（このときのシャッフルの置換を$r$とする）
6. $\tau$を適用していない方を開示して、それにより$r\tau\sigma$を並び換えて$\rho = \sigma^{-1}\tau\sigma$を得る
7. 同様の操作で$\rho, \rho^2, \dots, \rho^r$を得る
8. プレイヤー$i$は$\rho, \rho^2, \dots, \rho^r$から$i$番目のカードをドローし、所属を表すカードと他のメンバーを得る

# まとめ

このようにすることで、カードによる秘密グループ分けをMental Pokerを用いて実装することができることが分った。秘密グループ分けはゲームマスターなし人狼において重要な役割をはたすが、今回の方法によりゲームマスターなし人狼（[Mental Jinro](http://qiita.com/yyu/items/8c10fcdbc17084ac2674)）をMental Pokerのうえで実装できる可能性が高まった。
また、グループ分けを公平な第三者なしで実行するプロトコルは様々な応用が考えられるので、これを用いて何か有用なプロトコルを検討したい。

# 参考文献

- カードを用いた秘匿グループ分けプロトコル
- [A TTP-free mental poker protocol achieving player confidentiality](http://qiita.com/yyu/items/8d8c82ba729b06b26e67)
- [Contribution to Mental Poker](http://www.tdx.cat/bitstream/handle/10803/5804/jcr1de1.pdf)
- [代数学IIのテキスト](http://sci.kj.yamagata-u.ac.jp/~waki/jpn/GroupText.pdf)
- [Charm-Crypt](http://www.charm-crypto.com/index.html)
