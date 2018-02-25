# はじめに

[Java で higher kinded polymorphism を実現する](http://qiita.com/lyrical_logical/items/2d68d378a97ea0da88c0)を読み、これをSwiftに移植すれば何かの役に立つかもしれないと考えた。この記事の完全なソースコードはGitHubの次のリポジトリから入手できる。

- https://github.com/y-yu/higher-kinded-polymorphism-in-swift

この記事を読んで疑問や改善点がある場合には、気軽にコメントなどで教えて欲しい。

# Higher Kinded Polymorphismとは？

*Higher Kinded Polymorphism*は日本語で**高階多相**などと呼ばれるもので、例えばSwiftで次のようなプロトコル`Functor`[^functor]を作成したいとする。

[^functor]: `Functor`は関数型界隈で意味のある言葉だが、この記事では`Functor`が何を意味するのかを知っていなくてもよい。

```swift
protocol Functor {
    associatedtype F
    associatedtype E
    
    func mapF<B>(_ f: (E) -> B) -> F<B>
}
```

型パラメータ`F`には、たとえば`Array`や`Set`など何か型パラメータを取るような型パラメータを用いる。しかしSwiftはこのような何か型パラメータを取るような型パラメータを書くことができず、次のようにコンパイルエラーとなる。

```
Cannot specialize non-generic type 'Self.F'
```

たとえばプログラム言語Scalaではこれをこのように書くことができる。

```scala
trait Functor {
  type F[_]
  type E
  
  def mapF[B](f: E => B): F[B]
}
```

このように、型パラメータが何かの型パラメータを取ることで、型パラメータ`F`が`Array`や`Set`など何であっても動作するような抽象的な関数を定義できるようになる。このような多相性のことをHigher Kinded Polymorphismと呼ぶ。

# SwiftでHigher Kinded Polymorphism

まず、次のようなクラス`App`とプロトコル`Newtype1`を作る。

```swift:App.swift
class App<T, A> {
    var underlying: Any
    
    init(_ a: Any) {
        underlying = a
    }
}
```

```swift:Newtype.swift
protocol Newtype1 {
    associatedtype T
    associatedtype A
    
    func inj() -> App<T, A>
}

extension Newtype1 {
    func inj() -> App<T, A> {
        return App(self)
    }
}
```

クラス`App`は2つの型パラメータを取り、コンストラクターに渡された引数をメンバ変数`underlying`に格納しておく。また、プロトコル`Newtype1`は関数`inj`を提供し、これは`App<T, A>`への変換を表す。
これらを利用してたとえば`Array`を高階に扱いたいときは次のようにする。

```swift:Array.swift
class ArrayConstructor { }

extension Array: Newtype1 {
    typealias T = ArrayConstructor
    typealias A = Element
}

extension App where T: ArrayConstructor {
    func prj() -> Array<A> {
        return (self.underlying as! Array<A>)
    }
}
```

このようにすることで、次の2つの操作が可能となる。

- 任意の型`A`について、`Array<A>`から関数`inj`で`App<ArrayConstructor, A>`へ変換する
- 任意の型`A`について、`App<ArrayConstructor, A>`から関数`prj`で`Array<A>`へ変換する

このようにすることで、今まで具体的になっていない型`Array`を型パラメータとして渡すことはできなかったが、クラス`App`と`ArrayConstructor`を利用して`App<ArrayConstructor, A>`という形で渡せるようになった。
同様に二分木を表す`Tree`についても次のように作ることができる。まずは`Tree`を次のように定義する。

```swift:Tree.swift
indirect enum Tree<Element> {
    case Leaf
    case Node(l: Tree<Element>, a: Element, r: Tree<Element>)
    
    func toString() -> String {
        switch self {
        case .Leaf:
            return "L"
        case let .Node(l, a, r):
            return "N(\(l.toString()), \(a), \(r.toString()))"
        }
    }
}
```

そして次のようにエクステンションを定義する。

```swift:Tree.swift
class TreeConstructor { }

extension Tree: Newtype1 {
    typealias T = TreeConstructor
    typealias A = Element
}

extension App where T: TreeConstructor {
    func prj() -> Tree<A> {
        return (self.underlying as! Tree<A>)
    }
}
```

これらを利用して最初に例として挙げたプロトコル`Functor`を作成する。まずプロトコル`Functor`を次のように定義する。

```swift:Functor.swift
protocol Functor {
    associatedtype F
    associatedtype E
    
    func mapF<B>(_ f: (E) -> B) -> App<F, B>
}
```

最初の例と異なり、`Functor`は最後の結果を`App<F, B>`という型で返すようしている。
型`Array`の値がプロトコル`Functor`の関数`mapF`が利用できるように、次のようなコードを実装する。

```swift:Functor.swift
extension Array: Functor {
    typealias F = ArrayConstructor
    typealias E = Element
    
    func mapF<B>(_ f: (E) -> B) -> App<F, B> {
        return self.map(f).inj()
    }
}
```

`Tree`の場合はやや複雑だが次のようになる。

```swift:Functor.swift
extension Tree: Functor {
    typealias F = TreeConstructor
    typealias E = Element
    
    private func loop<B>(_ x: Tree<E>, _ f: (E) -> B) -> Tree<B> {
        switch x {
        case .Leaf:
            return .Leaf
        case let .Node(l, a, r):
            return Tree<B>.Node(l: loop(l, f), a: f(a), r: loop(r, f))
        }
    }
    
    func mapF<B>(_ f: (E) -> B) -> App<F, B> {
        return loop(self, f).inj()
    }
}
```

最後に、本当に`Array`や`Tree`から関数`mapF`が呼び出せるのかを確認する。

```swift:main.swift
print( [1, 2, 3, 4, 5].mapF({ (x: Int) -> Int in return x + 1 }).prj() )

let tree: Tree<Int> =
    .Node(
        l: .Node(l: .Leaf, a: 1, r: .Leaf),
        a: 2,
        r: .Node(l: .Leaf, a: 3, r: .Leaf)
    )

print( tree.mapF({ (x: Int) -> Int in return x + 1 }).prj().toString() )
```

これは次の2つの結果を求める。

- `Int`の配列の全ての要素を$+1$した配列を表示する
- `Int`の二分木の全ての要素を$+1$した二分木を表示する

結果は次のようになる。

```
[2, 3, 4, 5, 6]
N(N(L, 2, L), 3, N(L, 4, L))
```

このように、正しく関数`mapF`が実行できていることが分かる。

# まとめ

このようにしてSwiftでもHigher Kinded Polymorphismを実現することができた。今回は`Array`や`Tree`のような型パラメータを1つ取るような型のみを例に挙げたが、たとえば`Either`のような2つの型パラメータを取る型もクラス`App`を入れ子にして`Newtype2`を作ることで同様に実装できると考えられる。これらによってより高度なプログラムを書くことができればいいと思う。

# 参考文献

- [Java で higher kinded polymorphism を実現する](http://qiita.com/lyrical_logical/items/2d68d378a97ea0da88c0)
- [Lightweight higher-kinded polymorphism](https://www.cl.cam.ac.uk/~jdy22/papers/lightweight-higher-kinded-polymorphism.pdf)
