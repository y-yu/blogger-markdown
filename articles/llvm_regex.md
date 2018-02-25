[正規表現技術入門](http://www.amazon.co.jp/dp/4774172707)という本の中に、正規表現のJITコンパイルという技術が紹介されている。VM型の正規表現エンジンは以前作った[^vm_engine]ので、これをLLVMへコンパイルすればおもしろいのではないかと考えて、実行することにした。なお、実装にはScalaを用いた。

> 追記：
> また、JVMのバイトコードへJITコンパイルする実験も書きました。
> [正規表現のJITコンパイラを実装する](http://qiita.com/yyu/items/3c4deb39d6b0a7955572)

[^vm_engine]: [VM型の正規表現エンジンを実装する](http://qiita.com/yyu/items/84b1a00459408d1a7321)を参照。

# 正規表現の抽象構文木

VMの実装の時に用いたものと同じく、次のデータ構造を用いる。

```scala
sealed trait Regex
case object Empty                  extends Regex
case class Let(c: Char)            extends Regex
case class Con(a: Regex, b: Regex) extends Regex
case class Alt(a: Regex, b: Regex) extends Regex
case class Star(a: Regex)          extends Regex
```

例えば正規表現`sa*(ba*ba*)*a*e`を上記のデータ型（抽象構文木）で表すと次のようになる。

```
Con(Con(Let('s'), Con(Con(Star(Let('a')), Star(Con(Con(Let('b'), Star(Let('a'))), Con(Let('b'), Star(Let('a')))))), Star(Let('a')))), Let('e'))
```

正規表現から抽象構文木への変換は、今回も人間が手動[^regex_parser]で行うことにする。

[^regex_parser]: @kmizu さんと @koizuka さんに、正規表現から抽象構文木へのパーサを作っていただいたので、そちらを利用することもできる。[コメント](http://qiita.com/yyu/items/a0ef2d2204c137707f3f#comment-af7f9a78cf6fb5b0a84d)を参考にするとよい。

# LLVM機械語の表現

LLVMの機械語の中から今回使うものを選び、それをデータ構造として次のように表現する。今回扱うLLVMの命令は木構造にならないので、正規表現（の抽象構文木）から直接機械語（文字列）を生成してもよかったが、デバッグが大変になるような気がしたので一旦LLVMの機械語を表現するデータへと変換してから、それを機械語（文字列）へ変換することにする。この機械語を表現するデータのことを、この記事では **機械語表現** と呼ぶ。

## レジスタと値

まず、レジスタと値を表現するデータ型を次のように表現する。

```scala
sealed trait Value
case class RInt(n: Int)            extends Value
case class RStr(s: String)         extends Value
case class VInt(n: Int)            extends Value
case class BA(f: String, l: Value) extends Value
```

それぞれ次のような意味となっている。

<dl>
  <dt><code>RInt(n)</code></dt>
  <dd>$n$番目のレジスタ（<code>%10</code>など）<dd>
  <dt><code>RStr(s)</code></dt>
  <dd>名前が <i>s</s> のレジスタ（<code>%hoge</code>など）</dd>
  <dt><code>VInt(n)</code></dt>
  <dd>整数値$n$</dd>
  <dt><code>BA(f, l)</code></dt>
  <dd>ラベルを表わす値</dd>
</dl>

## 型

続いて、LLVMで今回扱う型をデータ型で表現する。

```scala
sealed trait Type
case object I1   extends Type
case object I8   extends Type
case object I8P  extends Type
case object I64  extends Type
case object I64P extends Type
```

それぞれ数字が整数値のビット長である。`P`が付くものはポインタを表す。

## 条件

比較を行う際に必要な条件を表すデータ型である。

```scala
sealed trait Cond
case object Eq extends Cond
```

実装してみて分かったが、今回は`Eq`しか使わなかったのでこのデータ型を用意する必要はなかったかもしれない。


## 命令

LLVMの命令の中で、今回用いるものを次のように表現する。

```scala
sealed trait Inst
case class Label(n: Value)                                    extends Inst
case class Assign(l: Value, r: Inst)                          extends Inst
case class Add(t: Type, v: Value, n: Int)                     extends Inst
case class Cmp(c: Cond, t: Type, a: Value, b: Value)          extends Inst
case class Br1(d: Value)                                      extends Inst
case class Br2(c: Value, t: Value, e: Value)                  extends Inst
case class Call(f: String, rt: Type, at: List[(Type, Value)]) extends Inst
case class Load(t: Type, p: Value)                            extends Inst
case class Store(vt: Type, v: Value, pt: Type, pv: Value)     extends Inst
case class GetElementPtr(t: Type, v: Value, i: Value)         extends Inst
```

まず、`Br1`と`Br2`は両方ともラベルへジャンプする命令を表している。これらの違いは、`Br1`は指定されたラベルはジャンプする命令であるのに対して、`Br2`はまず二値のレジスタを受けとり、その結果に応じてそれぞれへジャンプするというものである。
また、`GetElementPtr`は配列などからインデックス$i$の値が格納されているアドレスを取得する命令である。
その他の命令については、たぶんなんとなく分かると思うので省略する。

# 正規表現から機械語表現への変換

## 実装方針の概要

前回の記事や[Regular Expression Matching: the Virtual Machine Approach](https://swtch.com/~rsc/regexp/regexp2.html)で紹介されているVMは二つのレジスタを使っていた。

<dl>
  <dt>PC</dt>
  <dd>次に実行するバイトコードの位置</dd>
  <dt>SP</dt>
  <dd>マッチを行う文字の位置</dd>
</dl>

このVMは次のような手順でマッチングを行う。

1. _PC_ の位置にあるバイトコードを取り出す（フェッチ）
2. バイトコードを命令`char`、`split`、`jmp`、`match`のどれかへディスパッチ
3. 命令に対応する処理を実行
4. _PC_ を更新

機械語へ変換することでバイトコードが機械語になり、それをCPUか何かが実行する形になるので、バイトコードをフェッチする必要はなくなる。よって _PC_ はなくすことができる。では`split`や`jmp`のように、どこか特定の場所から命令を実行したくなった場合、 _PC_ なしでどうするのか疑問に思うかもしれない。このような場合は、マッチを行うLLVM上の関数に**ラベル**を引数として渡し、それを使って好きな場所から命令を開始できるようにする。
LLVM上でマッチングを行う関数を`@test`とすると、それは次のような型を持つ。

```llvm
define i1 @test(i8* %str, i8* %l, i64 %sp_value)
```

第一引数が文字列のポインタで、第二引数がラベルのポインタ、そして第三引数が _SP_ となる。

## 補助関数

次のような補助関数を定義しておく。

```scala
def nsp    = RStr("sp")
def nstr   = RStr("str")
def nmatch = RStr("match")
def nmiss  = RStr("miss")

def fname = "@test"

def assign(r: Inst, n: Int): (Inst, Int) = (Assign(RInt(n), r), n + 1)
def mk_label(n: Int): (Inst, Int) = (Label(RInt(n)), n + 1)
```

`n`から始まるものは機械語の中でよく使われる変数やラベルである。

## 実装

正規表現の種類（文字、連接、選択、繰り返し）に対応して次のように機械語表現を生成する。

### 文字

```scala
case Let(c) =>
  val (i1, n1) = mk_label(n)
  val (i2, n2) = assign(Load(I64P, nsp), n1)
  val (i3, n3) = assign(GetElementPtr(I8P, nstr, RInt(n1)), n2)
  val (i4, n4) = assign(Add(I64, RInt(n1), 1), n3)
  val  i5      = Store(I64, RInt(n3), I64P, nsp)
  val (i6, n5) = assign(Load(I8P, RInt(n2)), n4)
  val (i7, n6) = assign(Cmp(Eq, I8, RInt(n4), VInt(c.toInt)), n5)
  val  i8      = Br2(RInt(n5), RInt(n6), nmiss)
  (List(i1, i2, i3, i4, i5, i6, i7, i8), n6)
```

これは次のことをする機械語表現を生成する。

1. ラベルを生成する
2. スタックにある _SP_ の値を読み込む
3. 文字列`nstr`の位置 _SP_ にある文字のアドレスを取得する
4. _SP_ の値に$1$を足し、それをスタックの _SP_ に保存する
5. (3)で取得したアドレスにある文字を取得する
6. (5)で取得した文字と、`c`を比較[^to_int]する
7. 等しければ次へ遷移し、間違っていたら`nmiss`へ遷移する

[^to_int]: LLVMでは文字と文字の比較はできないので、`c`をASCIIコードに基づく数字へ変換して数字と数字の比較を行っている。

### 連接

```scala
case Con(a, b) =>
  val (i1, n1) = loop(a, n)
  val (i2, n2) = loop(b, n1)
  (i1 ++ i2, n2)
```

単に両側にある正規表現を機械語表現へ変換して、それらを結合する。

### 選択

```scala
case Alt(a, b) =>
  val (i1, n1) = mk_label(n)
  val (i2, n2) = assign(Load(I64P, nsp), n1)
  val (i3, _)  = assign(Call(fname, I1, List((I8P, BA(fname, RInt(n2 + 1))), (I64, RInt(n1)))), n2)
  val (i4, n4) = loop(a, n2 + 1)
  val (i5, n5) = mk_label(n4)
  val (i6, n6) = loop(b, n5)
  val i7       = Br1(RInt(n6))
  val i8       = Br2(RInt(n2), nmatch, RInt(n5))
  (List(i1, i2, i3, i8) ++ i4 ++ List(i5, i7) ++ i6, n6)
```

これは次のことをする機械語表現を生成する。

1. ラベルを生成する
2. スタックにある _SP_ の値を読み込む
3. 選択の左側（正規表現`a`）を機械語表現へコンパイルする
4. (3)の機械語表現に、選択の右側（`b`）の処理をスキップする機械語表現を追加する
5. 選択の右側（正規表現`b`）を機械語表現へコンパイルする
6. `@test`を再帰的に呼び出す。この時`a`を表す機械語表現のラベルを渡す
7. (5)が成功すればマッチ成功へ遷移し、そうでなければ`b`を表す機械語表現のラベルへジャンプする

### 繰り返し

```scala
case Star(Star(r)) => loop(Star(r), n)

case Star(r) =>
  val (i1, n1) = mk_label(n)
  val (i2, n2) = assign(Load(I64P, nsp), n1)
  val (i3, _)  = assign(Call(fname, I1, List((I8P, BA(fname, RInt(n2 + 1))), (I64, RInt(n1)))), n2)
  val (i4, n3) = loop(r, n2 + 1)
  val (i5, n4) = mk_label(n3)
  val  i6      = Br1(RInt(n))
  val  i7      = Br2(RInt(n2), nmatch, RInt(n4))
  (List(i1, i2, i3, i7) ++ i4 ++ List(i5, i6), n4)
```

まず、無限ループを回避する[^avoid_nonstop_loop]ために、二重になった繰り返しを除去する。そして、次のことをする機械語表現を生成する。

[^avoid_nonstop_loop]: [前回の記事（加筆部分）](http://qiita.com/yyu/items/84b1a00459408d1a7321#%E8%BF%BD%E8%A8%98%E4%BA%8C%E9%87%8D%E3%81%AE%E7%B9%B0%E3%82%8A%E8%BF%94%E3%81%97%E3%81%A7%E3%82%B9%E3%82%BF%E3%83%83%E3%82%AF%E3%82%AA%E3%83%BC%E3%83%90%E3%83%BC%E3%83%95%E3%83%AD%E3%83%BC)を参照。

1. ラベルを生成する
2. スタックにある _SP_ の値を読み込む
3. 繰り返しの中身（正規表現`r`）を機械語表現へコンパイルする
4. (3)の機械語表現の末尾に、(1)で生成したラベルへジャンプする命令を追加する
5. `@test`を再帰的に呼び出す。この時`r`を表す機械語表現のラベルを渡す
6. (5)が成功すればマッチ成功へ遷移し、次の命令のラベルへジャンプする

# 機械語表現から機械語への変換

機械語表現から機械語（文字列）へ変換するプリンタを次のように定義する。機械語表現に対応して説明する。

## レジスタと値

LLVMの機械語ではレジスタやラベルの先頭に`%`を付けるので、次のようにする。ただし、ラベルをプリントする際は`%`を付けない。

```scala
def label_of_value(v: Value): String = v match {
  case RInt(n) => n.toString
  case _       => throw new Exception()
}

def var_of_value(v: Value): String = v match {
  case RInt(n)  => "%" + n
  case RStr(s)  => "%" + s
  case VInt(n)  => n.toString
  case BA(f, l) => "blockaddress(" + f + ", " + var_of_value(l) + ")"
}
```

## 条件

```scala
def pp_cond(c: Cond): String = c match {
  case Eq => "eq"
}
```

## 型と型のサイズ

型と、`load`や`store`の際に必要となる型のサイズに関する変換を次のように定義する。

```scala
def pp_type(t: Type): String = t match {
  case I1   => "i1"
  case I8   => "i8"
  case I8P  => "i8*"
  case I64  => "i64"
  case I64P => "i64*"
}

def align(t: Type): Int = t match {
  case I8   => 1
  case I8P  => 8
  case I64  => 8
  case I64P => 8
  case I1   => throw new Exception()
}
```

## 命令

機械語表現を次のように機械語へ変換する。

```scala
def pp_inst(i: Inst, tab: String = ""): String =
  tab + (i match {
    case Label(n) =>
      "\n; <label>:" + label_of_value(n)
    case Assign(l, r) =>
      var_of_value(l) + " = " + pp_inst(r)
    case Add(t, v, n) =>
      "add nsw " + pp_type(t) + " " + var_of_value(v) + ", " + n
    case Cmp(c, t, a, b) =>
      "icmp " + pp_cond(c) + " " + pp_type(t) + " " + var_of_value(a) + ", " + var_of_value(b)
    case Br1(d) =>
      "br label " + var_of_value(d)
    case Br2(c, t, e) =>
      "br i1 " + var_of_value(c) + ", label " + var_of_value(t) + ", label " + var_of_value(e)
    case Call(f, rt, a) =>
      val s = a.foldLeft("i8* %str")((x, y) => x + ", " + pp_type(y._1) + " " + var_of_value(y._2))
      "call " + pp_type(rt) + " " + f + "(" + s + ")"
    case Load(t, p) =>
      "load " + pp_type(t) + " " + var_of_value(p) + ", align " + align(t)
    case Store(vt, v, pt, pv) =>
      "store " + pp_type(vt) + " " + var_of_value(v) + ", " + pp_type(pt) + " " +
        var_of_value(pv) + ", align " + align(vt)
    case GetElementPtr(t, v, i) =>
      "getelementptr inbounds " + pp_type(t) + " " + var_of_value(v) + ", i64 " + var_of_value(i)
  })
```

## 機械語として必要な命令を追加する

これで命令をコンパイルすることはできたが、LLVMとしての体裁を保つためにいくつか必要な機械語（例えば`main`関数や、`printf`関数を使うための諸々など）を追加する`make`という関数を定義する。

```scala
def make(i: List[Inst]): String = {
  val s =
    "@.match   = private unnamed_addr constant [7 x i8] c\"match\\0A\\00\", align 1\n"  +
    "@.unmatch = private unnamed_addr constant [9 x i8] c\"unmatch\\0A\\00\", align 1\n\n" +
    "define i1 @test(i8* %str, i8* %l, i64 %sp_value) {\n" +
    "  %sp = alloca i64, align 8\n" +
    "  store i64 %sp_value, i64* %sp, align 8\n" +
    "  %isnull = icmp eq i8* %l, null\n" +
    "  br i1 %isnull, label %1, label %jump\n\n" +
    "jump:\n" +
    "  indirectbr i8* %l, [" +
      i.foldRight(List[String]())((x, y) => x match {
        case Label(n) => ("label " + var_of_value(n)) :: y
        case _        => y
      }).mkString(", ") + "]\n"

  val llvmir = i.map(pp_inst(_, "  ")).foldLeft("")((x, y) => x + y + "\n")

  val e =
    "\nmiss:\n" +
    "  ret i1 0\n\n" +
    "match:\n" +
    "  ret i1 1\n" +
    "}\n\n" +
    "define i32 @main(i32 %argc, i8** %argv) {\n" +
    "  %arg1 = getelementptr inbounds i8** %argv, i64 1\n" +
    "  %str  = load i8** %arg1, align 8\n" +
    "  %res  = call i1 @test(i8* %str, i8* null, i64 0)\n" +
    "  br i1 %res, label %match, label %unmatch\n\n" +
    "match:\n" +
    "  call i32 (i8*, ...)* @printf(i8* getelementptr inbounds ([7 x i8]* @.match, i32 0, i32 0))\n" +
    "  br label %ret\n\n" +
    "unmatch:\n" +
    "  call i32 (i8*, ...)* @printf(i8* getelementptr inbounds ([9 x i8]* @.unmatch, i32 0, i32 0))\n" +
    "  br label %ret\n\n" +
    "ret:\n" +
    "  ret i32 0\n" +
    "}\n\n" +
    "declare i32 @printf(i8*, ...)"

  s + llvmir + e
}
```

# 具体例

今回のコードは[Gist](https://gist.github.com/yoshimuraYuu/8fba01232bfcc05656c5)に置いてあるほか、[ideone](https://ideone.com/ahuaWI)で実行することができる。

試しに偶数個の _b_ と任意の数の _a_ からなる文字列にマッチする正規表現`sa*(ba*ba*)*a*e`[^s_and_e]に対応するLLVMのコードを生成する。まず、この正規表現を次のような抽象構文木へ手動[^regex_parser]で変換する。

[^s_and_e]: この正規表現には文字列の開始や終端を表す方法がないので、与えられる文字列が _s_ から始まり _e_ で終わると仮定し開始と終端を擬似的に表現している。

```
Con(Con(Let('s'), Con(Con(Star(Let('a')), Star(Con(Con(Let('b'), Star(Let('a'))), Con(Let('b'), Star(Let('a')))))), Star(Let('a')))), Let('e'))
```

これを先程のScalaで書いたコンパイラに投入すると、次のようなLLVMのコードが得られる。

```llvm
@.match   = private unnamed_addr constant [7 x i8] c"match\0A\00", align 1
@.unmatch = private unnamed_addr constant [9 x i8] c"unmatch\0A\00", align 1

define i1 @test(i8* %str, i8* %l, i64 %sp_value) {
  %sp = alloca i64, align 8
  store i64 %sp_value, i64* %sp, align 8
  %isnull = icmp eq i8* %l, null
  br i1 %isnull, label %1, label %jump

jump:
  indirectbr i8* %l, [label %1, label %7, label %10, label %16, label %17, label %20, label %26, label %29, label %35, label %36, label %42, label %45, label %51, label %52, label %53, label %56, label %62, label %63, label %69]
  
; <label>:1
  %2 = load i64* %sp, align 8
  %3 = getelementptr inbounds i8* %str, i64 %2
  %4 = add nsw i64 %2, 1
  store i64 %4, i64* %sp, align 8
  %5 = load i8* %3, align 8
  %6 = icmp eq i8 %5, 115
  br i1 %6, label %7, label %miss
  
; <label>:7
  %8 = load i64* %sp, align 8
  %9 = call i1 @test(i8* %str, i8* blockaddress(@test, %10), i64 %8)
  br i1 %9, label %match, label %17
  
; <label>:10
  %11 = load i64* %sp, align 8
  %12 = getelementptr inbounds i8* %str, i64 %11
  %13 = add nsw i64 %11, 1
  store i64 %13, i64* %sp, align 8
  %14 = load i8* %12, align 8
  %15 = icmp eq i8 %14, 97
  br i1 %15, label %16, label %miss
  
; <label>:16
  br label %7
  
; <label>:17
  %18 = load i64* %sp, align 8
  %19 = call i1 @test(i8* %str, i8* blockaddress(@test, %20), i64 %18)
  br i1 %19, label %match, label %53
  
; <label>:20
  %21 = load i64* %sp, align 8
  %22 = getelementptr inbounds i8* %str, i64 %21
  %23 = add nsw i64 %21, 1
  store i64 %23, i64* %sp, align 8
  %24 = load i8* %22, align 8
  %25 = icmp eq i8 %24, 98
  br i1 %25, label %26, label %miss
  
; <label>:26
  %27 = load i64* %sp, align 8
  %28 = call i1 @test(i8* %str, i8* blockaddress(@test, %29), i64 %27)
  br i1 %28, label %match, label %36
  
; <label>:29
  %30 = load i64* %sp, align 8
  %31 = getelementptr inbounds i8* %str, i64 %30
  %32 = add nsw i64 %30, 1
  store i64 %32, i64* %sp, align 8
  %33 = load i8* %31, align 8
  %34 = icmp eq i8 %33, 97
  br i1 %34, label %35, label %miss
  
; <label>:35
  br label %26
  
; <label>:36
  %37 = load i64* %sp, align 8
  %38 = getelementptr inbounds i8* %str, i64 %37
  %39 = add nsw i64 %37, 1
  store i64 %39, i64* %sp, align 8
  %40 = load i8* %38, align 8
  %41 = icmp eq i8 %40, 98
  br i1 %41, label %42, label %miss
  
; <label>:42
  %43 = load i64* %sp, align 8
  %44 = call i1 @test(i8* %str, i8* blockaddress(@test, %45), i64 %43)
  br i1 %44, label %match, label %52
  
; <label>:45
  %46 = load i64* %sp, align 8
  %47 = getelementptr inbounds i8* %str, i64 %46
  %48 = add nsw i64 %46, 1
  store i64 %48, i64* %sp, align 8
  %49 = load i8* %47, align 8
  %50 = icmp eq i8 %49, 97
  br i1 %50, label %51, label %miss
  
; <label>:51
  br label %42
  
; <label>:52
  br label %17
  
; <label>:53
  %54 = load i64* %sp, align 8
  %55 = call i1 @test(i8* %str, i8* blockaddress(@test, %56), i64 %54)
  br i1 %55, label %match, label %63
  
; <label>:56
  %57 = load i64* %sp, align 8
  %58 = getelementptr inbounds i8* %str, i64 %57
  %59 = add nsw i64 %57, 1
  store i64 %59, i64* %sp, align 8
  %60 = load i8* %58, align 8
  %61 = icmp eq i8 %60, 97
  br i1 %61, label %62, label %miss
  
; <label>:62
  br label %53
  
; <label>:63
  %64 = load i64* %sp, align 8
  %65 = getelementptr inbounds i8* %str, i64 %64
  %66 = add nsw i64 %64, 1
  store i64 %66, i64* %sp, align 8
  %67 = load i8* %65, align 8
  %68 = icmp eq i8 %67, 101
  br i1 %68, label %69, label %miss
  
; <label>:69
  br label %match

miss:
  ret i1 0

match:
  ret i1 1
}

define i32 @main(i32 %argc, i8** %argv) {
  %arg1 = getelementptr inbounds i8** %argv, i64 1
  %str  = load i8** %arg1, align 8
  %res  = call i1 @test(i8* %str, i8* null, i64 0)
  br i1 %res, label %match, label %unmatch

match:
  call i32 (i8*, ...)* @printf(i8* getelementptr inbounds ([7 x i8]* @.match, i32 0, i32 0))
  br label %ret

unmatch:
  call i32 (i8*, ...)* @printf(i8* getelementptr inbounds ([9 x i8]* @.unmatch, i32 0, i32 0))
  br label %ret

ret:
  ret i32 0
}

declare i32 @printf(i8*, ...)
```

生成されたLLVMの機械語をエディタなどに貼り付けて、ここでは _regex.ll_ という名前で保存する。そしてコンピューターにLLVMをインストールして次のようなコマンドを実行する。

```console
$ llc regex.ll && gcc regex.s
```

成功すると _a.out_ というプログラムができているので、それのコマンドライン引数にマッチさせたい文字列を与えれば、マッチングを行うことができる。

```console
$ ./a.out saabbaabbe
match

$ ./a.out saabbaabbabe
unmatch
```

# まとめ

最小の正規表現をLLVMへ変換するコードは規模で言えば200行程度なので、割とシンプルに書けたと思う。今回はシンプルに実装することが目標だったのでベンチマークなどは取っていないが、何かの実装と比べてみるのもおもしろいかもしれない。

# 参考文献

- [正規表現技術入門](http://www.amazon.co.jp/dp/4774172707)
- [Regular Expression Matching: the Virtual Machine Approach](https://swtch.com/~rsc/regexp/regexp2.html)
- [きつねさんでもわかるLLVM ~コンパイラを自作するためのガイドブック~](http://www.amazon.co.jp/dp/4844334158)
- [LLVM Language Reference Manual](http://llvm.org/docs/LangRef.html)

# 関連文献

- [正規表現はお好き?](http://steps.dodgson.org/bn/2007/12/15/)
- [Rubyによる正規表現コンパイラ(その2)](http://d.hatena.ne.jp/miura1729/20080925/1222330236)
