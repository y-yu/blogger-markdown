# はじめに

Minimal Cake Pattern[^mcp]とは、株式会社ドワンゴの一部で採用されているDI（Dependency Injection）の手法である。このMinimal Cake Patternは主にScalaで行われている手法であるが、この記事ではこの手法をSwiftに移植することを目指す。
この記事で紹介したソースコードは次のリポジトリに置かれている。

https://github.com/y-yu/MinimalCakePatternInSwift

もしこの記事を読んで、疑問や改善するべき点を見つけた場合は、気軽にコメントなどで指摘して欲しい。

[^mcp]: この手法は、“mix-in injection”とも呼ばれているが、この記事ではMinimal Cake Patternを用いることにする。

# Minimal Cake Patternとは？

こちらの記事に詳細な解説があるので、まずはこちらを読んでいただきたいが、DIについての知識がある場合は飛ばしてもよい。

[Scalaにおける最適なDependency Injectionの方法を考察する 〜なぜドワンゴアカウントシステムの生産性は高いのか〜](http://qiita.com/pab_tech/items/1c0bdbc8a61949891f1f)

# SwiftによるMinimal Cake Pattern

例として「ファイルを読み込んで、その内容と読み込んだ時刻を合せて返すサービス」の作成を例に説明していく。また、もしファイルの読み込みに失敗した場合は、適切なログを出す必要があるものとする。

## 時刻を返す

現在の時刻を単純に取得してしまうと、その部分のテストを作る時に、テストを実行する時間によっては成功したり失敗したりする不味いテストになる可能性がある。そこで、時間を取得するインターフェースを作り、DIができるようにする。

```swift:Clock.swift
protocol Clock {
    func now() -> NSDate
}
```

このインターフェースは`now`というメソッドを持ち、このメソッドが時間を返すものとなっている。これを用いて、現在の時刻を返す実装と、テスト用の実装を次のようにそれぞれ定義する。

```swift:Clock.swift
class MixInSystemClock: Clock {
    func now() -> NSDate {
        return NSDate()
    }
}

class MixInMockClock: Clock {
    let date: NSDate
    
    init(_ str: String) {
        let inputFormatter = NSDateFormatter()
        inputFormatter.dateFormat = "yyyy-MM-dd"
        date = inputFormatter.dateFromString(str)!
    }
    
    func now() -> NSDate {
        return date
    }
}
```

`SystemClock`は現在の時刻を返すようになっているが、`MockClock`は引数で時刻を受け取り、`now`メソッドは必ずそれを返すようになっている。
次に、この`Clock`を用いることを示すインターフェースを次のように定義する。

```swift:Clock.swift
protocol UsesClock {
    var clock: Clock { get }
}
```

## ログを出力する

ログは、ファイルに出力するべき時もある一方で、テストの際はファイルIOの失敗によりテストが失敗することを防ぐために、ロガーが呼ばれたことだけをチェックし、ログは標準出力に出せば十分であることがある。このように、いろいろな実装が考えられることから、ロガーについてもDIできた方がよい。`Clock`と同様に、まずはロガーのインターフェースを次のように定義する。

```swift:Logger.swift
protocol Logger {
    func info(m: String) -> Void
    
    func error(m: String) -> Void
}
```

そして、今回は標準出力にログを出力する実装だけを用意する。

```swift:Logger.swift
class MixInPrintLogger: Logger {
    func info(m: String) -> Void {
        print("Info: " + m)
    }
    
    func error(m: String) -> Void {
        print("Error: " + m)
    }
}
```

最後に、このロガーを使うことを表すインターフェースを定義する。

```swift:Logger.swift
protocol UsesLogger {
    var logger: Logger { get }
}
```

## ファイルを読み込むサービス

さて、時刻を取得する部分とログを出す部分が完成したので、次はファイルを読み込むサービスを作る。まず、このサービスはファイルを読み込んで、内容と時刻を返すメソッド`readWithDate`を持つことを示すインターフェースを定義する[^option]。

```swift:ReadFileService.swift
protocol ReadFileService: UsesClock, UsesLogger {
    func readWithDate(fileName: String) -> Optional<(NSDate, String)>
}
```

[^option]: このメソッドは、もしファイルの読み込みに失敗したら`None`を返す。

このインターフェースは`UsesClock`と`UsesLogger`を実装しなければならないので、このインターフェースの実装にもしDIが行われていなければコンパイルに失敗することになる。Minimal Cake Patternのような静的なDIは、このようにDIに失敗したことをコンパイルタイムに教えてくれるというメリットがある。そして、`readWithDate`メソッドの内容を次のように与える。

```swift:ReadFileService.swift
extension ReadFileService {
    func readWithDate(fileName: String) -> Optional<(NSDate, String)> {
        if let dir : NSString = NSSearchPathForDirectoriesInDomains(NSSearchPathDirectory.DocumentDirectory, NSSearchPathDomainMask.AllDomainsMask, true).first {
            
            let pathFileName = dir.stringByAppendingPathComponent(fileName)
            logger.info(pathFileName)
            
            do {
                let text = try NSString(contentsOfFile: pathFileName, encoding: NSUTF8StringEncoding)
                return (clock.now(), text as String)
            } catch {
                logger.error("fail to read the file!")
                return Optional.None
            }
        } else {
            logger.error("fail to search directory to read the file!")
            return Optional.None
        }
    }
}
```

このメソッドの中では、`UsesClock`と`UsesLogger`により、時刻の取得とログの出力が抽象的に行える。さて、これに具体的な実装をDIすると、次のようになる。

```swift:ReadFileService.swift
class MixInReadFileService: ReadFileService {
    var clock: Clock = MixInSystemClock()
    var logger: Logger = MixInPrintLogger()
}

class MixInReadFileServiceTest: ReadFileService {
    var clock: Clock = MixInMockClock("2016-06-18")
    var logger: Logger = MixInPrintLogger()
}
```

このように、デフォルトの実装である`MixInReadFileService`では現在の時刻を返す`MixInSystemClock`がDIされている。一方で、テストで使う`MixInReadFileServiceTest`は`MixInMockClock`で常に現在時刻が2016年6月18日となるようにしている。これで、テストが時間によって成功したり失敗したりするという事態を回避することができる。

## `ReadFileService`を使う`MainService`

さて、`ReadFileService`を使って`test.txt`の中身を表示`MainService`を考える。次のように、まずはインターフェースを定義する。

```swift:main.swift
protocol MainService: UsesReadFileService {
    func main() -> Void
}
```

そして、メソッドの内容を与える。

```swift:main.swift
extension MainService {
    func main() -> Void {
        let opt = readFileService.readWithDate("test.txt")
        _ = opt.map({(f: (NSDate, String)) -> Void in
            print(f.0)
            print(f.1)
        })
    }
}
```

そして、具体的な実装をDIして終了である。

```swift:main.swift
class MixInMainService: MainService {
    var readFileService: ReadFileService = MixInReadFileService()
}
```

## `MainService`を使う

`MainService`の実装である`MixInMainService`を次のように使う。

```swift:main.swift
MixInMainService().main()
```

もし`test.txt`が存在する場合は、次のような出力が得られる。

```
Info: /Users/hikaru_yoshimura/Documents/test.txt
2016-06-18 10:24:20 +0000
foobar
hogehoge
```

存在しない場合、次のようにエラーログが出力される。

```
Info: /Users/hikaru_yoshimura/Documents/test.txt
Error: fail to read the file!
```

# まとめ

このように、Minimal Cake PatternをSwiftでも用いることができた。DIについて、Swift界隈でも議論が起きればよいと思う。

# 参考文献

- [Scalaにおける最適なDependency Injectionの方法を考察する 〜なぜドワンゴアカウントシステムの生産性は高いのか〜](http://qiita.com/pab_tech/items/1c0bdbc8a61949891f1f)
- [Mix-in injection における最強のテスト用インスタンス構築パターン](http://qiita.com/tayama0324/items/6ff7cb937a4283789ed8)
- [Minimal Cake Pattern のお作法](http://qiita.com/tayama0324/items/7f87ee3672b15dd68016)
- [Swift2で静的なDIを実現する謎のソースコード](http://qiita.com/gomi_ningen/items/3b977fbc83bcac2fc6f2)
