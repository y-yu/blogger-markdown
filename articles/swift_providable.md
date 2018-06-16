# はじめに

[@Nonchalant](https://twitter.com/nonchalant0303)さんの[FactoryProvider](https://github.com/Nonchalant/FactoryProvider)というSwiftのテスト支援ライブラリーを見て、もしかしたらデータの作成をもうちょっと面白くできるのではないかと考えて、彼のライブラリーを**Stateモナド**と**HList**を利用して改造してみたのでそれをここに示す。この記事ではHListとStateモナドについて軽く解説し、どのようにこれらを利用しているかについて説明する。なお、この記事の完全なソースコードは下記のリポジトリにある。

- https://github.com/y-yu/FactoryProvider

この記事を読んで分かないことや質問などがある場合には、気軽にコメントなどで教えて欲しい。

# 使い方

作成したライブラリーの詳しい説明する前に、これがどのように使えるのかについて説明する。たとえば次のようにテスト用のデータを作ることができる。

```swift:main.swift
let a =
    String.provide() >>>
    Bool.provide() >>>
    Optional<Int>.provide() >>>
    end()

let (b, _) = a.run(0)

print(b.head, b.tail.head, b.tail.tail.head as Any)
```

これを実行すると次のように表示される。

```
0 false Optional(2)
```

たとえば同じ`Int`を連続で生成しても、違う値となるようになっている。

```swift:main.swift
let c =
    Int.provide() >>>
    Int.provide() >>>
    Int.provide() >>>
    end()

let (d, _) = c.run(0)

print(d.head, d.tail.head, d.tail.tail.head as Any)
```

これは次のようになる。

```
0 1 2
```

これがどのようなトリックで作られているかについて解説する。ちなみに再代入可能な値をグローバルに更新している、といったものではない。

# 状態を用いたテストデータの生成

ここでは`Int`の`provide`メソッドを例とするが、もし`Int.provide`が引数を取ってよいとしたら、これは簡単に実装できそうだ。

```swift
protocol Providable {
    associatedtype S

    static func provide(s: S) -> (Self, S)
}
```

プロトコル`Providable`はそれに準拠した型の値を、状態を表す型`S`を利用して生成する。ただ、結果は自身の型である`Self`と次の状態を返すようになっている。たとえば`Providable`の状態を`Int`、そして生成したい型も`Int`で実装すると次のようになる。

```swift
extension Int: Providable {
    typealias S = Int

    static func provide(s: Int) -> (Int, Int) {
        return (s, s + 1)
    } 
}
```

これを使えば次のように書ける。

```swift
let (i1, s1) = Int.provide(0)
let (i2, s2) = Int.provide(s1)
let (i3, s3) = Int.provide(s2)

print(i1, i2, i3)
```

すると次のようになる。

```
0 1 2
```

このようにすることで、別々となるような`Int`型のデータを作ることができる。

# Stateモナド

たしかにこれでもよいといえばよいが、変数がたくさんあって大変である。これを解決させるために**Stateモナド**を利用する。Stateモナドとは次のようなデータ構造である。

```swift:State.swift
public struct State<S, A> {
    public let run : (S) -> (A, S)
    
    public init(_ run : @escaping (S) -> (A, S)) {
        self.run = run
    }
    
    func flatMap<B>(_ f: @escaping (A) -> State<S, B>) -> State<S, B> {
        return State<S, B> {
            (s: S) -> (B, S) in
                let (a, s1) = self.run(s)
                return f(a).run(s1)
        }
    }
    
    func map<B>(_ f: @escaping (A) -> B) -> State<S, B> {
        return State<S, B> {
            (s: S) -> (B, S) in
                let (a, s1) = self.run(s)
                return (f(a), s1)
        }
    }
}
```

構造体`State`の第1型パラメータ`S`は状態の型であり、そして第2型パラメータ`A`は生成される結果の型である。これを利用して、プロトコル`Providable`を次のように書きかえることができる。

```swift:Providable.swift
public protocol Providable {
    associatedtype S
    
    static func provide() -> State<S, Self>
}
```

つまり、メソッド`provide`は型`S`の状態を利用してプロトコルを実装した型を返すので、さきほどの引数を取る実装とそれほど変っていない。同じように`Int`で実装すると次のようになる。

```swift:ProvidableInstance.swift
extension Int: Providable {
    public typealias S = Int
    
    public static func provide() -> State<Int, Int> {
        return State<Int, Int>{
            (s: Int) -> (Int, Int) in (s, s + 1)
        }
    }
}
```

`provide`メソッドが状態を取るかわりに、構造体`State`のラムダ式[^lambda]として状態が引数で渡されて結果と次の状態を返すという構造は変っていない。これを利用して次のように書くことができる。

[^lambda]: ラムダ計算の用語に則るならば、ここでは「ラムダ抽象」が適切ではあるが一般に浸透した言葉としてここでは「ラムダ式」とした。

```swift
let ((i1, i2, i3), _) =
    Int.provide().flatMap { i1 in
        Int.provide().flatMap { i2 in
            Int.provide().map { i3 in (i1, i2, i3) }
        }
    }.run(0)

print(i1, i2, i3)
```

```
0 1 2
```

これで最初にあった変数がたくさん必要となる問題は解決した。

# HListと`>>>`演算子

関数がネストして大変なことになっている。そこで**HList**を利用してこれを解決する。HListとは次のようなプロトコルである。

```swift:HList.swift
public protocol HList { }
public struct HNil: HList {
    init() { }
}

public struct HCons<H, T: HList>: HList {
    public let head: H
    public let tail: T
    
    public init(_ h: H, _ t: T) {
        self.head = h
        self.tail = t
    }
}
```

プロトコル`HList`は2つの構造体`HNil`と`HCons`を持つ。これは、端的に言えば次のような特徴を持つ。

- 一般のリストとは違い、どのような型のデータも挿入することができる
- どの型がリスト上のどの位置（インデックス）にあるかを型レベルで記憶している

たとえば`HCons<Int, HCons<String, HCons<Bool, HNil>>>`とは、先頭の値の型が`Int`であり、かつ2番目の値の型が`String`であり、そして3番目の値の型が`Bool`であることを示している。これを用いて`>>>`演算子を次のように定義する。

```swift:Providable.swift
precedencegroup Right {
    associativity: right
}

infix operator >>>: Right

public func >>><S, A, T: HList>(_ ma: State<S, A>, _ mb: State<S, T>) -> State<S, HCons<A, T>> {
    return ma.flatMap {
        (a: A) -> State<S, HCons<A, T>> in
            mb.map {
                (t: T) -> HCons<A, T> in HCons<A, T>(a, t)
            }
    }
}

public func end<S>() -> State<S, HNil> {
    return State<S, HNil> {
        s -> (HNil, S) in (HNil(), s)
    }
}
```

`>>>`演算子は左側に型`A`を作るStateモナドをとり、左側にはなんらかのHListである`T`を作るStateモナドを取り、結果として`HCons<A, T>`という型の値を返すStateモナドを返す。そして関数`end`は`HNil`を作るStateモナドを返す。これにより、最初の例のような方法でネストを抑えながら次々に値を生成できる。

```swift:main.swift
let c =
    Int.provide() >>>
    Int.provide() >>>
    Int.provide() >>>
    end()

let (d, _) = c.run(0)

print(d.head, d.tail.head, d.tail.tail.head as Any)
```

ちなみに型情報も失われていないので、IDEできちんと表示される。

<img width="294" alt="image" src="https://qiita-image-store.s3.amazonaws.com/0/10815/0157ba08-92b9-3b04-de2b-34cc633efc13.png">

# まとめ

StateモナドとHListを利用することで、ネストが異常な量になるなどといったシンタクッス上の綺麗さも保ちつつ、しかし常に同じ値ではなく値を更新しながら作るといったことができるようになった。たとえば常に同じ値にしたい場合は、状態の型`S`を`Void`といった型にしてしまって、状態を使わずに作成することで達成できそうである。

