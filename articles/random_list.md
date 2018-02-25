> この記事にあるコードは下記のGistにまとめてあります。
> https://gist.github.com/yoshimuraYuu/96ca584da1d04efb248b

例えば数字$0, 1, \dots, 25$からアルファベット$a, b, \dots, z$へ変換するために次のようなリストを定義したとします。

```ocaml
let alphabet = ['a'; 'b'; 'c'; 'd'; 'e'; 'f'; 'g'; 'h'; 'i'; 'j'; 'k'; 'l'; 'm'; 'n'; 'o'; 'p'; 'q'; 'r'; 's'; 't'; 'u'; 'v'; 'w'; 'x'; 'y'; 'z']
```

ここでは例として、1から25までの数字で構成されたリストを受け取って、それを上記のリストを用いて文字のリストへ変換する関数を作るとします。

# 直感的な実装

まず、リストを先頭から調べていって$n$番目の要素を返す関数`nth`を定義します [^why_does_implement_nth]。

[^why_does_implement_nth]: OCamlには`List.nth`という機能が同じ関数がありますが、ここでは`nth`の動作を分かりやすくするために、あえて再実装しました。

```ocaml
let rec nth l = function
    0   ->  List.hd l
|   i   ->  nth (List.tl l) (i - 1) 

```

この`nth`を使って、入力されたリストに対応するリスト`alphabet`の要素を返す関数を次のように定義します。

```ocaml
let rec trans1 = function
    []      -> []
|   x::xs   -> nth alphabet x :: trans1 xs
```

まず`nth`は$n$回再帰するので、計算量$O(n)$の関数ということになります。その関数をリストの長さ分呼び出している`trans1`の計算量は、リストの長さを$n$、要素の平均を$m$とすると$O(n \times m)$という計算量になります。

次のようなテストする関数で試してみます。この関数は引数`l`と`n`を取り、`trans1 l`を$n$回繰り返す関数です。

```ocaml
let rec test1 l = function
    0   -> ();
|   i   -> 
        let _ = trans1 l in
        test1 (i - 1)
```

次の例を`time`コマンドでどれくらいかかるのか測定してみます。

```ocaml
test1 [1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1] 1000000
```

```console
$ time ocaml trans.ml
ocaml trans.ml  2.09s user 0.01s system 99% cpu 2.101 total
```

一方で、この例は大変なことになります。

```ocaml
test1 [25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25] 1000000
```

```console
$ time ocaml trans.ml
ocaml trans.ml  15.36s user 0.02s system 99% cpu 15.503 total
```

この差を埋めるのが当面の目標です。

# 効率的な実装

リストを「インデックスでソートされた二分木」へ変換します。
まずは木を次のように定義します。`N`はノードで`L`はリーフを表します。

```ocaml
type 'a tree =
    L of 'a
|   N of int * 'a tree * 'a tree
```

二分探索のように、要素を半分半分にしていく関数を定義します。

```ocaml
let join = function
    ((L _) as t1), ((L _) as t2)                  -> N(2, t1, t2)
|   ((L _) as t1), ((N(n, _, _)) as t2) |
    ((N(n, _, _)) as t1), ((L _) as t2)           -> N(n + 1, t1, t2)
|   ((N(n1, _, _)) as t1), ((N (n2, _, _)) as t2) -> N(n1 + n2, t1, t2)

let rec inner = function
    []          -> []
|   x::[]       -> [x]
|   x::(y::xs)  -> (join (x, y)) :: inner xs

let rec build_tree = function
    x::[]       -> x
|   xs          -> build_tree (inner xs)
```

複雑ですが、イメージはこんな感じです。

![buil_tree_reduce.png](https://qiita-image-store.s3.amazonaws.com/0/10815/d31cc28e-3bd5-a2f4-1592-f51f6f47a795.png)

アルファベットのリストを一旦二分木へ変換すると、次のようになります。

```ocaml
# build_tree (List.map (fun x -> L x) alphabet);;
- : char tree =
N (26,
 N (16,
  N (8, N (4, N (2, L 'a', L 'b'), N (2, L 'c', L 'd')),
   N (4, N (2, L 'e', L 'f'), N (2, L 'g', L 'h'))),
  N (8, N (4, N (2, L 'i', L 'j'), N (2, L 'k', L 'l')),
   N (4, N (2, L 'm', L 'n'), N (2, L 'o', L 'p')))),
 N (10,
  N (8, N (4, N (2, L 'q', L 'r'), N (2, L 's', L 't')),
   N (4, N (2, L 'u', L 'v'), N (2, L 'w', L 'x'))),
  N (2, L 'y', L 'z')))
```

この二分木から$n$番目の文字を取り出す関数を次のように定義します。

```ocaml
let rec extract_tree = function
    0, N(_, (L e), r)     -> e
|   1, N(2, (L _), (L r)) -> r
|   n, N(_, (L _), r)     -> extract_tree (n - 1, r)
|   n, N(n1, l, (L e)) when n + 1 == n1 -> e
|   n, N(c, (N(cl, _, _) as l), r) ->
        if n < cl then
            extract_tree (n, l)
        else
            extract_tree (n - cl, r)
|   _   -> failwith "error"
```

まず、`extract_tree`に`0`と左がリーフの木が渡された場合、左側の木の要素を返します。

![extract1_reduce.png](https://qiita-image-store.s3.amazonaws.com/0/10815/e6672c19-2b20-972f-8743-c17defb7cb8d.png)

次に左がリーフで右もリーフの大きさ2の木に対して、`1`が入力された場合は次のようになります。

![extract2_reduce.png](https://qiita-image-store.s3.amazonaws.com/0/10815/b54450a8-c615-eadd-98ce-0d35f5d2a2f1.png)

左がリーフで右がノードの場合、右のノードを再帰的に調べていきます。

![extract3_reduce.png](https://qiita-image-store.s3.amazonaws.com/0/10815/be4c92fa-2008-0a01-f53e-e127e2152f21.png)

左がノードで右がリーフの場合、次のような条件で右のリーフの要素を返します。

![extract4_reduce.png](https://qiita-image-store.s3.amazonaws.com/0/10815/8d59aacc-df44-7adf-e15b-0a8d3a5cb72b.png)

右と左が両方ノードである場合は入力`n`に応じて次の二つに分岐します。

![extract5_reduce.png](https://qiita-image-store.s3.amazonaws.com/0/10815/c3a0dcaf-2069-7258-5465-711e632406f7.png)

しっかり取り出せるのかを、次のコードで検証します。

```ocaml
let alphabet_tree = build_tree (List.map (fun x -> L x) alphabet)
let check_extract_tree () = 
    let rec loop i =
        if i > 25 then []
        else extract_tree (i, alphabet_tree) :: loop (i + 1)
    in
    loop 0
```


```ocaml
# check_extract_tree ();;
- : char list =
['a'; 'b'; 'c'; 'd'; 'e'; 'f'; 'g'; 'h'; 'i'; 'j'; 'k'; 'l'; 'm'; 'n'; 'o';
 'p'; 'q'; 'r'; 's'; 't'; 'u'; 'v'; 'w'; 'x'; 'y'; 'z']
```

そして、数字のリストからアルファベットのリストへ変換する効率的な関数を定義します。

```ocaml
let rec trans2 l =
    match l with
        []      -> []
    |   x::xs   -> extract_tree (x, alphabet_tree) :: trans2 xs
```

テスト用のコードを用意します。

```ocaml
let rec test2 l = function
    0   -> ();
|   i   -> 
        let _ = trans2 l in
        test2 l (i - 1);;
```

それではテストです。

```ocaml
test2 [1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1] 1000000
```

```console
$ time ocaml trans.ml
ocaml trans.ml  9.55s user 0.01s system 99% cpu 9.557 total
```

どれくらいの差があるでしょうか。

```ocaml
test2 [25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25; 25] 1000000
```

```console
$ time ocaml trans.ml
ocaml trans.ml  5.64s user 0.01s system 99% cpu 5.652 total
```

`test1`に比べて差が少ないようです。

# 結論

リストから二分木へ変換する計算量は、リストの長さを$n$として$O(\log_2(n))$です。この二分木から要素を取り出す計算量は$O(\log_2(n))$なので、`trans2 l`は`l`の長さを$m$とすると、$O\left((m + 1) \log_2(n)\right)$ということになります。
直感的な実装の計算量が$O(n \times m)$なので、こちらの実装の方が効率的であると言えそうです。

# 参考文献

- [Provably perfect shuffle algorithms](http://okmij.org/ftp/Haskell/perfect-shuffle.txt)
