# はじめに

JSONなどを用いてデータを受け渡ししていると、しばしば様々な型のキーとバリューが組み合さったDictionaryを作りたくなるときがある。しかし、`Dictionary<AnyKey, AnyObject>`のようなものを使ってしまうと、危険なダウンキャストを行わなれけばならず、プログラムがランタイムに異常終了する可能性が高まる。そこで、この記事ではいろいろな型のキーやバリューが格納できる**安全**なDictionaryであるHDic（Heterogeneous Dictionary）を作ることを目標とする。このHDicはプログラマが入れられるキーとバリューの型を制御することができ、許可した型のキーとバリューはどれだけでも入れたり出したりできる一方で、許可のないものでアクセスした場合はコンパイルに失敗するというものになっている。
この記事を読んで分からないことや、疑問点や改善するとよい部分を見つけた場合は、コメントなどで気軽に教えて欲しい。
なお、この記事で公開されているコードは次のリポジトリから入手できる。

https://github.com/y-yu/HDic


# `Dictionary[AnyKey, AnyObject]`

まず安全ではないが、いろいろな型のキーとバリューがを出し入れできるDictionaryを作ることにする。
Swiftはキーがプロトコル`Hashable`を実装していなければならない。まずは[StackOverflowの記事](http://stackoverflow.com/questions/24119624/how-to-create-dictionary-that-can-hold-anything-in-key-or-all-the-possible-type)を参考に、次のような`Hashable`の実装を用意する。

```swift:AnyKey.swift
// see http://stackoverflow.com/questions/24119624/how-to-create-dictionary-that-can-hold-anything-in-key-or-all-the-possible-type
struct AnyKey: Hashable {
    var underlying: Any
    var hashValueFunc: () -> Int
    var equalityFunc: (Any) -> Bool
    
    init<T: Hashable>(_ key: T) {
        underlying = key
        hashValueFunc = { key.hashValue }
        equalityFunc = {
            if let other = $0 as? T {
                return key == other
            }
            return false
        }
    }
    
    var hashValue: Int { return hashValueFunc() }
}

func == (x: AnyKey, y: AnyKey) -> Bool {
    return x.equalityFunc(y.underlying)
}
```

これは次のようにすることで、`Hashable`なものを`AnyKey`にすることができる。

```swift
var a = AnyKey(1)
var b = AnyKey("string")
var c = AnyKey(true)
```

これを使えば、なんら型安全ではないが、ひとまずあらゆる型のキーとバリューを挿入できるDictionaryを次のように定義できる。

```swift
var dic = Dictionary<AnyKey, AnyObject>()
dic[AnyKey("string")] = true
dic[AnyKey(true)]     = 1
```

しかし、これは型情報が失われて全部が`AnyObject`になってしまうので、次のようにダウンキャストを使って取り出すしかない。

```swift
dic[AnyKey("string")] as! Bool
```

# アクセス可能なキーとバリューの組を表す`Relation`

危険なダウンキャストを避けるために、まず次のようなプロトコルを導入する。

```swift:Relation.swift
protocol Relation {
    associatedtype Me = Self
    associatedtype Key
    associatedtype Value
}
```

これは、自身の型`Me`とキーとバリューの型の組を表す簡単なプロトコルである。これを用いて、型安全なDictionaryである`HDic`を定義する。

# 安全なDictionaryである`HDic`の定義

次のように定義する。

```swift:HDic.swift
struct HDic<R: Relation> {
    let underlying: Dictionary<AnyKey, AnyObject>
    
    internal init(_ dic: Dictionary<AnyKey, AnyObject> = Dictionary<AnyKey, AnyObject>()) {
        underlying = dic
    }

    func _get<K: Hashable, V>(k: K) -> Optional<V> {
        return(underlying[AnyKey(k)] as? V)
    }
    
    func _add<K: Hashable, V>(k: K, v: V) -> HDic<R> {
        var n = self.underlying
        n.updateValue(v as! AnyObject, forKey: AnyKey(k))
        return HDic(n)
    }
}
```

`HDic`は基本的には`Dictionary<AnyKey, AnyObject>`のラッパーである。また、`_get`や`_add`はどんな型のキーやバリューでも入れたり出したりできるので、これらをそのまま使うと危険なことになってしまう。そこで、この`_get`や`_add`のラッパーを用意する。

# `HDic`への安全なアクセス

`HDic`が取る型パラメータ`R`とは、さきほど作ったプロトコル`Relation`の実装である。これは次のように適当に実装すればよい。

```swift:main.swift
struct ConcreteRelation: Relation {
    typealias Key = Any
    typealias Value = Any
}
```

そして、これを用いて`HDic`を初期化する。

```swift
var h1 = HDic<ConcreteRelation>()
```

次のように`extension`を使って`HDic`へのアクセスを許可する型を決める。

```swift:main.swift
extension HDic where R.Me == ConcreteRelation, R.Key == String, R.Value == String {
    func get(k: String) -> Optional<String> {
        return _get(k)
    }
    
    func add(k: String, v: String) -> HDic<R> {
        return _add(k, v: v)
    }
}

extension HDic where R.Me == ConcreteRelation, R.Key == Int, R.Value == Int {
    func get(k: Int) -> Optional<Int> {
        return _get(k)
    }
    
    func add(k: Int, v: Int) -> HDic<R> {
        return _add(k, v: v)
    }
}
```

まず、上に書かれたextensionは、関係`R`が`ConcreteRelation`であり、キーが`String`でバリューも`String`である組のアクセスを可能にするための仕組みであり、下はキーとバリューがそれぞれ`Int`と`Int`の組に対するものである。
このように、extensionを追加すれば、既存の`Int`や`String`以外のプログラマが定義した型についても設定できる。
そして、正しくアクセス制御ができているかを確認する。

```swift:main.swift
var h1 = HDic<ConcreteRelation>()
var h2 = h1.add("string", v: "string")
var h3 = h2.add(2, v: 1)
var h4 = h3.add("str", v: true)  // compile time error!
h3.get(true) // compile time error!

print(h3.get("string")) // Optional("string")
```

このように、先ほど定義したキーが`String`でバリューも`String`なものと、キーが`Int`でバリューも`Int`なもの以外は挿入することができないし、または`Bool`型の値`true`で`get`を実行してもコンパイルエラーとなる。

## 他のアクセスとの同居

`ConcreteRelation`とは違った種類のアクセスを同居させる場合は、次のようにすればよい。まず、もうひとつのキーとバリューの型の関係を定義する。

```swift:main.swift
struct AnotherRelation: Relation {
    typealias Key = Any
    typealias Value = Any
}
```

定義内容は`ConcreteRelation`と全く同じだが、名前が異なるので`ConcreteRelation`とは別物である。そして、extensionを次のように定義する。

```swift:main.swift
extension HDic where R.Me == AnotherRelation, R.Key == Bool, R.Value == Bool {
    func get(k: Bool) -> Optional<Bool> {
        return _get(k)
    }

    func add(k: Bool, v: Bool) -> HDic<R> {
        return _add(k, v: v)
    }
}
```

これは、関係が`AnotherRelation`であり、キーの型が`Bool`でバリューの型が`Bool`であるようなアクセスを許可する。したがって、次のような動作となる。

```swift
var h1 = HDic<ConcreteRelation>()
var h2 = h1.add(true, v: false) // compile time error!

var h3 = HDic<AnotherRelation>()
var h4 = h3.add(true, v: false) // ok
```

このように、`ConcreteRelation`とは別の制御ができることが確認できる。このようにすることで、異なるアクセスを同居させることができる。

# まとめ

このように、extensionを用いて、特定のキーとバリューの型だけがアクセスできるような安全なDictionaryを作ることができた。ややボイラープレートが残ってしまったが、これを用いればより信頼性の高いプログラムを書くことができるかもしれない。
