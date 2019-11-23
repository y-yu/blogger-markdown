---
title: ScalaからJavaCPP + Java経由でネイティブライブラリーを使う
tags: Scala Java C++ JNI
author: yyu
slide: false
---
# はじめに

未踏ターゲット2018年度ゲート式量子コンピュータにおける開発でC++で主に書かれた量子コンピューターのシミュレーターである[Qulacs](https://github.com/qulacs/qulacs)を利用している。QulacsはPythonバインディングがすでに用意されているが、やはりより慣れたプログラム言語であるScalaで開発をしたいと常に思っていた。そこで[JavaCPP](https://github.com/bytedeco/javacpp)を利用してQulacsのようなネイティブライブラリーをJava経由でScalaから呼び出すために色々と調査したところ、最終的にはsbtプラグインを作ることができた。

- https://github.com/y-yu/sbt-javacpp4s

実はJavaCPPのGitHubオーガナイゼーションにもsbtプラグインがあるが、調べたところこれはJavaCPPですでに利用できるOpenCVなどをScalaから使いやすくするためのものであり、新規にネイティブライブラリーをScalaから利用できるようにするものではなかったため、今回新規に作成することとした。この記事ではこのsbtプラグインの使い方や一部の内部実装について解説する。
この記事を読んで分からないことや改善点がある場合は、気軽にコメントで教えてほしい。

# プラグインの概要

このsbtプラグインは次の3つを行う。

1. `.so`（または`.dylib`）のようなネイティブライブラリーを作成する
2. （1）のライブラリーとヘッダーファイルをJavaCPPに渡してJNI（Java Native Interface）用のファイルを作成する
3. （2）を`g++`のような処理系でコンパイルしてJavaから利用できるネイティブライブラリーを作成する

まず、（1）はライブラリーによってそれの作り方は（`make`を使うなど）色々異なると思われるので、sbtの`settingKey`としてOSコマンドをわたすようになっている。そして、（2）もまたsbtから新たなJavaプロセスを起動している。これはJVMへ渡すオプションを適宜変える必要があり、たしかにsbtの`run`コマンドや`javaOptions`などを適切に変更すれば達成できた可能性もあるが、労力のわりに最終的に起きることにたいした変わりがないということでこのようにした。そしてそのままJavaCPPが（3）を行いJavaから呼びだせるようなダイナミックリンクライブラリーとなる。

# 設定と使い方

ここからは[サンプルのプロジェクト](https://github.com/y-yu/sbt-javacpp4s/tree/master/example)を元に解説していく。今、C++のソースコードとヘッダーファイルが次のように存在するものする。

```cpp:cpp_src/HelloWorld.hpp
class HelloWorld {
public:
    int printN(int n);
};
```

```cpp:cpp_src/HelloWorld.cpp
#include <iostream>
#include <string>
#include "HelloWorld.hpp"

using namespace std;

int HelloWorld::printN(int n) {
    for (int i = 0; i < n; i++) {
        cout << "Hello World!\n";
    }

    return n;
}
```

まず、これをコンパイルするための設定を`build.sbt`へ記述する。


```scala:build.sbt
includePath := (baseDirectory in Compile).value / "cpp_src"

libraryName := "libHelloWorld"

makeLibraryCommands := Seq(
  gppCompilerPath.value,
  "-I", includePath.value.toString,
  currentLibraryMeta.value.option,
  "-o",
  (libraryDestinationPath.value / s"${libraryName.value}.${currentLibraryMeta.value.extension}").toString,
  ((baseDirectory in Compile).value / "cpp_src" / "HelloWorld.cpp").toString
)
```

ここで`makeLibraryCommands`が`libHelloWorld`を作成するために利用されるOSコマンドである。順番に解説していく。
まず`gppCompilerPath`はデフォルトで`clang++`が利用される。
次に`currentLibraryMeta`はOSによる`clang++`といった処理系のオプションと、生成されるネイティブライブラリーの拡張子を吸収するためのデータ構造`DynamicLibraryMeta`が保存されている。

```scala:DynamicLibraryMeta.scala
sealed abstract class DynamicLibraryMeta(
  val option: String,
  val extension: String
)

object DynamicLibraryMeta {
  case object Mac extends DynamicLibraryMeta("-dynamiclib", "dylib")
  case object Linux extends DynamicLibraryMeta("-shared", "so")
}
```

そして`currentLibraryMeta`はデフォルトはJavaのプロパティである`System.getProperty("os.name")`から自動で選択される。`libraryDestinationPath`もデフォルトでは`target`ディレクトリ下の専用ディレクトリを利用する。

次にネイティブライブラリーを利用するJavaコードを作る。

```java:src/main/java/javacpp/sbt/HelloWorld.java
package javacpp.sbt;

import org.bytedeco.javacpp.*;
import org.bytedeco.javacpp.annotation.*;

@Platform(include = {"HelloWorld.hpp"}, link = "HelloWorld")
public class HelloWorld extends Pointer {
    static {
        Loader.load();
    }

    public HelloWorld() {
        allocate();
    }

    public native void allocate();

    public native int printN(int n);
}
```

再び`build.sbt`へ戻り、ネイティブライブラリーと対応するJavaのクラスパスを与える。

```scala:build.sbt
nativeJavaClassPath := "javacpp.sbt.*"

enablePlugins(SbtJavaCPP4S)
```

このようにワイルドカードを使うこともできる。また今回のプラグインを有効にして`build.sbt`における作業は終了となる。

最後にScalaからJava部分の呼び出しコードを作っておく。

```scala:src/main/scala/javacpp/HelloWorld.scala
object HelloWorld {
  def main(args: Array[String]): Unit = {
    val instance = new HelloWorld()
    instance.printN(5)
  }
}
```

あとはこれを`sbt run`すると次のようになる。

```console
$ sbt run
[info] Loading settings for project example from build.sbt ...
[info] Set current project to example (in build file:/Users/yyu/Desktop/javacpp-sbt/example/)
[info] Compiling 1 Scala source to /Users/yyu/Desktop/javacpp-sbt/example/target/scala-2.12/classes ...
[info] Success!
[info] running (fork) org.bytedeco.javacpp.tools.Builder -cp /Users/yyu/Desktop/javacpp-sbt/example/target/scala-2.12/classes:/Users/yyu/Library/Caches/Coursier/v1/https/repo1.maven.org/maven2/org/bytedeco/javacpp/1.5.1/javacpp-1.5.1.jar:/Users/yyu/.sbt/boot/scala-2.12.10/lib/scala-library.jar -Dplatform.compiler=clang++ -Dplatform.includepath=/Users/yyu/Desktop/javacpp-sbt/example/cpp_src -Dplatform.linkpath=/Users/yyu/Desktop/javacpp-sbt/example/target/libjni -d /Users/yyu/Desktop/javacpp-sbt/example/target/libjni javacpp.sbt.*mple / Compile / generateJNILibrary 0s
[info] Generating /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/jnijavacpp.cpp
[info] Generating /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/jniHelloWorld.cpp
[info] Compiling /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/libjniHelloWorld.dylib
[info] clang++ -I/Users/yyu/Desktop/javacpp-sbt/example/cpp_src -I/Library/Java/JavaVirtualMachines/openjdk-11.0.2.jdk/Contents/Home/include -I/Library/Java/JavaVirtualMachines/openjdk-11.0.2.jdk/Contents/Home/include/darwin /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/jniHelloWorld.cpp /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/jnijavacpp.cpp -march=x86-64 -m64 -O3 -Wl,-rpath,@loader_path/. -Wall -fPIC -dynamiclib -undefined dynamic_lookup -o libjniHelloWorld.dylib -L/Users/yyu/Desktop/javacpp-sbt/example/target/libjni -Wl,-rpath,/Users/yyu/Desktop/javacpp-sbt/example/target/libjni -lHelloWorld -framework JavaVM
[info] Deleting /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/jniHelloWorld.cpp
[info] Deleting /Users/yyu/Desktop/javacpp-sbt/example/target/libjni/jnijavacpp.cpp
[info] running (fork) javacpp.HelloWorld
[info] Hello World!
[info] Hello World!
[info] Hello World!
[info] Hello World!
[info] Hello World!
[success] Total time: 6 s, completed 2019/11/09 4:57:50
```

このように上手く動作している。

# おわりに

小さな例では上手くいったので、次はQulacsのような大きなC++ライブラリーを扱えるようにしていきたい。今回の開発はコード量に対して大変な労力がかかっている。やはりネイティブのエラーをよく分かっていなかったり、ダイナミックリンクについて知っていなかったりと色々な苦労があった。余談となるがGo言語などがシングルバイナリとなっているのは、こういったダイナミックリンクの煩雑さも1つの要因ではないかと思う。

