# Introduction

*Ransomware* is one of the malicious programs (malware), which encrypts victim's data and requests money such as Bitcoins as ransom for decrypting the data stored in their computer. Recently, “WannaCry” has become popular worldwide. However, as a simple question, if a victim sends Bitcoins as ransom, will they be able to decrypt their encrypted data? In other words, current ransomware may make them lose both money and data.
In this article, we assume that there are Alice who is an author of a ransomware and she want to get Bitcoins, and Bob who has been infected with Alice's ransomware and his data has been encrypted. He wants to decrypt the data even though he pays Bitcoins to Alice, but the following two kinds of malicious action are possible between Alice and Bob. 

1. Alice first received Bitcoins from Bob, although she will not send the key to decrypt the ciphertext which Bob has
2. Bob gave the key to decrypt the ciphertext from Alice, although he will not send Bitcoins to her

We show that the *fair ransomware protocol* to prevent these malicious actions with a high probability. Also this protocol uses current Bitcoin's property and cryptographic techniques, so it does not require any trusted third party.
In the first section I will explain cryptographic techniques which are necessary for protocol configuration, and I will introduce Bitcoin in next section, then in the next section we will consider the precondition of Alice and Bob. Next I will explain the details of the fair ransomware protocol, finally I will talk the conclusion and the references.
Note that you can get the source code of this article from [here](http://qiita.com/yyu/items/02cab9a02053bc8d7e28.md).

# Cryptographic Techniques

In this section, I explain cryptographic techniques for constructing the protocol.

## Symmetric Key Encryption

*Symmetric key encryptions* are encryption schemes that use the same key for encrypting and decrypting. We can encrypt the any length data that is called a *plaintext* by the fixed length of the data that is called a *symmetric key*. We encrypt the data $x$ using a symmetric key $k$, in this article it will be written as follows by the $\text{Enc}$ as an encrypting function.

```math
\def\Enc#1#2{\text{Enc}_{#1}\left(#2\right)}
\def\Dec#1#2{\text{Dec}_{#1}\left(#2\right)}
\Enc{k}{x}
```

Using a decrypting function $\text{Dec}$, we able to decrypt a *ciphertext* which is the result of encrypting. We can decrypt if the symmetric key used for decryption is equal to the symmetric key used for encryption. So the following equation holds.

```math
x = \Dec{k}{\Enc{k}{x}}
```

But, symmetric key encryptions do not guarantee that $x = \Enc{k}{\Dec{k}{x}}$ which is that the order of encryption and decryption is switched.
Symmetric key encryptions are faster than public key encryptions like RSA encryption which will be described later. [AES](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) is one of the most famous implementation of symmetric key encryptions. And recently [ChaCha20](https://en.wikipedia.org/wiki/Salsa20#ChaCha20_adoption) has been proposed. This article's protocol does not require a specific implementation of symmetric key encryptions, so we write $\text{Enc}$ as the encrypting function of symmetric key encryption and $\text{Dec}$ as decrypting function of that.

## Hash Function

*Hash functions* output data of a fixed length for any length of data as input. For a hash function $H$, its return $H(x)$ of data $x$ is called a *hash value*. And for a hash value $h := H(m)$, $m$ is called the *preimage* of the hash value $h$. Hash functions have the following properties.

<dl>
  <dt>Pre-image resistance</dt>
  <dd>Given a hash value $h$ it should be difficult to find any message $m$ such that $h = H(m)$.</dd>

  <dt>Second pre-image resistance</dt>
  <dd>Given an input $m_1$ it should be difficult to find different input $m_2$ such that $H(m_1) = H(m_2)$.</dd>

  <dt>Collision resistance</dt>

  <dd>It should be difficult to find two different messages $m_1$ and $m_2$ such that $H(m_1) = H(m_2)$.</dd>
</dl>

In this protocol hash functions must be run on the Bitcoin scripts described later, so an implementation of the hash functions must be [SHA-1](https://en.wikipedia.org/wiki/SHA-1), [SHA-256](https://en.wikipedia.org/wiki/SHA-2) or [RIPEMD-160](https://en.wikipedia.org/wiki/RIPEMD). We write $H$ as a hash function, which is a SHA-1, SHA-256 or RIPEMD-160.

## RSA Encryption

*RSA encryption* is one of the public key encryption. Public key encryptions are encryption schemes that use two different keys for encryption and decryption, unlike symmetric key encryptions. We call a key used for encryption a *public key*, and a key used for decryption a *private key*. Using the public key in the RSA encryption as $(e, N)$, encrypting a plaintext $x$ is as follows.

```math
x^e \bmod N
```

$N$ is a product of different huge prime numbers $p, q$. If you know the prime factors $p, q$ of $N$, you can easily obtain a private key $d$ which holds the following equation.

```math
x = (x^e)^d = (x^d)^e \pmod{N}
```

Unlike symmetric key encryptions, you can restore the plaintext $x$ even if you switch the order of encrypting and decrypting. This property is used in signatures described later.
Those who do not know the prime factors $p, q$ of N, it is very difficult to obtain the private key $d$ from the public key $(e, N)$ and the ciphertext $x^e \bmod N$. If $N$ is 2048 bits or more, even attackers use supercomputers, the prime factorization takes enought time, so we think RSA encryption is safe.
Next we will describe some features of RSA encryption.

<dl>
  <dt>Plaintext size</dt>
  <dd>At the time of encrypting and decrypting, we calculate $\bmod N$ so that plaintext must be from $0$ to $N - 1$. If you want to encrypt the plaintext whose size is larger than $N - 1$, you must divide the plaintext for each $\log_2 N$ bits. 

  <dt>Blind and unblind</dt>
  <dd>A person who has a ciphertext can decrypt it whithout knowing the ciphertext. They <em>blind</em> a ciphertext and send to a person who has a secret key and decrypts it, then remove the blind (<em>unblind</em>).</dd>

  <dt>Signature</dt>
  <dd>RSA encryption can also be used for signing. <em>Signatures</em> are mechanisms to verify that certain data was created by a person who has a secret key (signature key) with a public key (verification key).</dd>
</dl> 

First, I will explain blind and unblind in detail. Now, Bob has a ciphertext $c$ encrypted by a public key $(e, N)$, Alice has a secret key $d$. But he does not want her to know the ciphertext $c$ and a plaintext $t$ which is the result of decrypting $c$.

1. Bob chooses a random number $r\; (1 \le r \lt N)$, $s := c \cdot r^e \bmod N$ and sends it to Alice
2. Alice calculates $\bar{s} := s^d \bmod N$ and sends it to Bob. In this case, $\bar{s}$ is as follows

    $$\bar{s} = s^d = (c \cdot r^e)^d = c^d \cdot (r^e)^d = c^d \cdot r \pmod {N}$$
3. Bob calculates $t := \bar{s} \, / \, r$. Therefore, $t = c^d \bmod N$

We can decrypt ciphertexts with keeping their secret by this way.
Next I explain signatures in detail. For example, there is a data $t$, Alice wants to show that this data was created by her to Bob. She has a secret key $d$. In addition, Alice and Bob know a public key $(e, N)$ and a hash function $H$.

1. Alice calculates $h: = H(t)$ and $s := h^d \bmod N$ and sends $t, s$ to Bob
2. Bob verifies the $H(t) = s^e \bmod N$. In this case, $s^e \bmod N$ is as follows:

    $$s^e = (h^d)^e = h \pmod{N}$$

Alice can caliculate $h^d \bmod N$ because she only knows the private key $d$. So she can prove that the data $t$ was created with her intention.
Signatures are used in Bitcoin, but Bitcoin uses [ECDSA](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm) instead of RSA because the efficiency is better than RSA. Nonetheless, in ECDSA we need not change the process of signing the data by a private key and verifying it by a public key.

## Zero-Knowledge Proof

*Zero-Knowledge proofs* are ways to prove that the proposition is true or false without being known other things. I will explain one of the *cut-and-choose protocol* which is a kind of Zero-Knowledge proofs. As a concrete method used in the fair rasomware protocol is described in later section, in this section I describe the intuition of the cut-and-choose protocol. The protocol proves as follows.

> Assuming that Bob has a data $c$, can Alice calculate the result of applying some function $f$ to the data $c$?

Alice wants to prove that she can calculate $f(c)$ to Bob, but she does not want Bob to know the details of the function $f$ and the result $f(c)$.

1. Bob computes the $n$ number data called _Fake Values_ $F$. However, Fake Values are calculated from only the random numbers and public information, they must not contain data $c$ which Bob has
2. Bob computes the $l$ number data called _Real Values_ $R$. However, Real Values are calculated from the random numbers and public information and the data $c$
3. Bob makes $\beta$ to concatenate Fake Values $F$ and Real Values $R$ and shuffle it
4. For $i := 1, \dots, n + l$, Alice calculates as follows:
    - Using a random number $k_i$, a ciphertext $s_i := \Enc{k_i}{f(\beta_i)}$
    - A hash value $h_i := H(k_i)$
5. Alice sends $s_1, \dots, s_{n + l}$ and $h_1, \dots, h_{n + l}$ to Bob
6. Bob sends Fake Values $F$ to Alice
7. Alice verifies that $\beta_i$ does not contain $c$ for all $i \in F$
8. Alice sends $k_i$ to Bob for all $i \in F$
9. For all $i \in F$, Bob verifies $h_i = H(k_i)$ and the decrypted value $\Dec{k_i}{s_i}$ is the result of applying the function $f$ 

We consider how they prove by this protocol. In (3) Alice does not know what the value is in the Real Values or the Fake Values. We assume that Alice cheat, using another function $g$, and now she caliculates the following manner.

```math
s_i: = \Enc{k_i}{g(\beta_i)}
```

However, in (9), if $\beta_i$ is one of the Fake Values, Alice must publish the symmetric key $k_i$ and the results of applying $f$ to Bob. Thus Bob knows that Alice did not calculate correctly. Indeed Alice applies $f$ only to the $n$ number Fake Values, then she applies a different function that is not $f$ to the $l$ number Real Values. But a probability of Alice's cheat to be successful is only one in the combination chosing the $n$ number of data from the $n + l$ number data. Therefore the probability is as follows.

```math
\frac{1}{%
  \left(\begin{array}{c}
    n + l\\
    n \\
  \end{array}\right)
}
```

So by setting $n$ and $l$ properly we can extremely reduce the probability of her cheat's success.
Also, when Bob uses the data $c$ falsely for the Fake Values and sends these to Alice, Bob gets the result $f(c)$ in (9). In order to avoid this Alice publishs a symmetric key $k_i$ after she verified the Fake Values sent from Bob in (7). This also prevents Bob's cheat.
This cut-and-choose protocol does not perform on any functions $f$, but it works very well with RSA encryption.

# Bitcoin

*Bitcoin* is a currency, unlike US dollar, which it does not have a central bank. Instead of a central bank, Bitcoin uses a *blockchain*, which is a ledger of *transactions*. The blockchain is managed by many people who are called *miners*. Miners verify each transaction. Only a transaction is verified successfully, it will be added to the blockchain. Anyone can become a miner and receives Bitcoins for verifying transactions.
How do the miners verify a transaction? They run programs called *scripts* which are included in the transaction. The script is a very restrictive non-Turing complete stack-based programming language, which does not include loops and recursions. For example, consider the following script.

```math
\begin{array}{l}
1 \\
2 \\
3 \\
\texttt{OP_ADD} \\
\texttt{OP_SUB} \\
\end{array}
%
%
%
\def\AtSOne#1\csod{%
	\begin{array}{c|}
		\hline
		#1\\
		\hline
	\end{array}
}%
\def\AtSTwo#1,#2\csod{%
	\begin{array}{c|c|}
		\hline
		#1 & #2\\
		\hline
	\end{array}
}%
\def\SOne#1{\AtSOne#1\csod}
\def\STwo#1{\AtSTwo#1\csod}
\def\AtSThree#1,#2,#3\csod{%
	\begin{array}{c|c|c|}
		\hline
		#1 & #2 & #3\\
		\hline
	\end{array}
}%
\def\AtSFour#1,#2,#3,#4\csod{%
	\begin{array}{c|c|c|c|}
		\hline
		#1 & #2 & #3 & #4\\
		\hline
	\end{array}
}%
\def\AtSFive#1,#2,#3,#4,#5\csod{%
	\begin{array}{c|c|c|c|c|}
		\hline
		#1 & #2 & #3 & #4 & #5\\
		\hline
	\end{array}
}%
\def\AtSSix#1,#2,#3,#4,#5,#6\csod{%
	\begin{array}{c|c|c|c|c|c|}
		\hline
		#1 & #2 & #3 & #4 & #5 & #6\\
		\hline
	\end{array}
}%
\def\SOne#1{\AtSOne#1\csod}
\def\STwo#1{\AtSTwo#1\csod}
\def\SThree#1{\AtSThree#1\csod}
\def\SFour#1{\AtSFour#1\csod}
\def\SFive#1{\AtSFive#1\csod}
\def\SSix#1{\AtSSix#1\csod}
\def\dosc#1#2\csod{{\rm #1{\scriptsize #2}}}
```

This works as follows. For the sake of clarity, we also show that the state of the stack after run each step.

1. Push $1$ to the stack $\SOne{1}$
2. Push $2$ to the stack $\STwo{2, 1}$
3. Push $3$ to the stack $\SThree{3, 2, 1}$
4. By $\texttt{OP_ADD}$, add the first value and the second value of the stack and push the result to the stack $\STwo{5, 1}$
5. By $\texttt{OP_SUB}$, subtract the first value and the second value of the stack and push the result to the stack $\SOne{4}$

Therefore, the final result of the execution of this script is $\SOne{4}$.

Transactions of Bitcoin have two scripts, `scriptPubKey` and `scriptSig`. For example, Bob wants to send 1 BTC which is given from Alice to Charlie. A transaction from Alice to Bob is $\textrm{Tx.1}$, also a transaction from Bob to Charlie is $\textrm{Tx.2}$. The requirement for accepting $\textrm{Tx.2}$ is as follows.

> Run `scriptSig` of $\textrm{Tx.2}$, then taking over the stack, run `scriptPubKey` of $\textrm{Tx.1}$, $\textrm{Tx.2}$ will be accepted unless the final stack is $\SOne{0}$. 

<img width="1039" alt="image.png" src="https://qiita-image-store.s3.amazonaws.com/0/10815/51d89290-be15-09ea-4953-3d6682f7bab3.png">

Unless the result of running `scriptSig` and `scriptPubKey` (eval) is $\SOne{0}$, the transaction $\textrm{Tx.2}$ accepts and will be added to the blockchain. We will consider that Bob sends 1 BTC which given from Alice as shown in the above figure. In addition, $\mathcal{B}$ is a public key that corresponds to Bob's Bitcoin address. `scriptSig` of $\textrm{Tx.2}$ contains Bob's signature $\mathbb{S}$ and his public key $\mathcal{B}$ as follows.

```math
\begin{array}{l}
\mathbb{S} \\
\mathcal{B}
\end{array}
```

After run this script, the stack are $\STwo{\mathcal{B}, \mathbb{S}}$, and then run `ScriptPubKey` the transaction $\textrm{Tx.1}$. This `scriptPubKey` is as follows.

```math
\begin{array}{l}
\texttt{OP_DUP} \\
\texttt{OP_HASH160} \\
h \\
\texttt{OP_EQUALVERIFY} \\
\texttt{OP_CHECKSIG}
\end{array}
```

The result of running this script under the stack $\STwo{\mathcal{B}, \mathbb{S}}$ is as follows.

1. By $\texttt{OP_DUP}$, copy the top of the stack $\SThree{\mathcal{B}, \mathcal{B}, \mathbb{S}}$
2. By $\texttt{OP_HASH160}$, caliculate a hash value of the top of the stack and push the hash value to the top of the stack $\SThree{H(\mathcal{B}), \mathcal{B}, \mathbb{S}}$
3. Push $h$ to the stack $\SFour{h, H(\mathcal{B}), \mathcal{B}, \mathbb{S}}$
4. By $\texttt{OP_EQUALVERIFY}$, compare the first value and the second value of the stack. If they are not equal immediately become failure $\STwo{\mathcal{B}, \mathbb{S}}$
5. By $\texttt{OP_CHECKSIG}$, verify the signature at the second of the stack by the public key at the top of the stack. If the verification is successful and push $1$ to the stack, if it fails push $0$ $\SOne{1}$ 

Bitcoin miners will accept the transaction if the result of the scripts is $\SOne{1}$, which means that $h = H(\mathcal{B})$ and the signature $\mathbb{S}$ is verified by the public key $\mathcal{B}$. Common Bitcoin transactions are done in this way.

# Precondition

Before describing the fair ransomware protocol, I will talk about Alice and Bob. Bob had data $t_1, \dots, t_m$, then they have been encrypted with a public key $(e, N)$ by Alice's ransomware. Now Bob has $c_1, \dots, c_m \; (c_i := (t_i)^e \bmod N)$. In addition, Bob knows the public key $(e, N)$ that was used in encrypting[^why_he_know]. Alice requests $x$ BTC as ransom for decrypting the Bob's data.
And Alice needs to think as follows.

[^why_he_know]: Bob can get the public key $(e, N)$ by reverse engineering Alice's ransomware.

> She will decrypt at least one amang encrypted Bob's data $c_1, \dots, c_m$ for free.

Why is such a condition necessary? Alice was able to execute arbitrary programs like ransomware on Bob's computer. Using the protocol described in the later section, Bob can decrypt his ciphertext by sending Bitcoins to Alice. However, Bob cannot decide whether the ciphertext is the result of encrypting the data stored in his computer, or the data created by Alice using random numbers. So Alice needs to decrypt at least one data for free, prove that Bob's ciphertext is the encrypted data originally stored in his computer. From this condition, the following condition are also derived at the same time.

> Bob can determine whether at least one data amang $t_1, \dots, t_m$ ware stored in his computer or not.

Since there are a lot of files on Bob's computer, the condition does not seem so unrealistic.
Finally, $\mathcal{A}$ is a public key that corresponds to Alice's Bitcoin address, also $\mathcal{B}$ is a public key that corresponds to Bob's Bitcoin address.

# Fair Ransomware Protocol

We will construct the fair ransomware protocol. This protocol consists of Phase 1, Phase 2 and Phase 3, and it is executed in this order. If any phase fails, the deal will be canceled immediately.

## Phase 1

In this phase, Bob will make sure that Alice can correctly decrypt a ciphertext $c_i$ specified by him.

1. Bob creates a random number $r\; (1 \le r \lt N)$, select a ciphertext $c_i$ which is able to identify that the content is correct and he caliculates $s := c_i \cdot r^e \bmod N$ then he sends $s$ to Alice
2. Alice caliculates $\bar{s} := s^d \bmod N$ using the secret key $d$ and sends $\bar{s}$ to Bob
3. Bob confirms $t_i = \bar{s} \, / \, r \bmod N$

First, Bob blinds the ciphertext $c_i$ in (1). It means that Bob makes Alice not know what ciphertext he tries to decrypt. If Bob sends the ciphertext $c_i$ to Alice to decrypt, in (2) she can return Bob's data which she stole from his computer in advance. In order to prevent this, Bob needs to blind the ciphertext which he wants to decrypt.
If Alice left the $i$ number data which Bob cannot decrypt amang all date $t_1, \dots, t_m$ as her cheat, in this case, the probability of this to be successful is the number of cases that Bob chooses other than $i$ number data, so it is as follows.

```math
\frac{m - i}{m}
```

Alice's cheat will be successful if $i$ is small relative to $m$, but it means Bob can decrypt a lot of data.

## Phase 2

In this phase Alice will prove that all ciphertexts that Bob has can be decrypted with the same secret key by the cut-and-choose protocol. First, a prover Alice who wants to prove the proposition and a verifier Bob who wants to verify the proposition have the following knowledge.

<dl>
  <dt>Prover Alice</dt>
  <dd>Alice knows the private key $d$ for the public key $(e, N)$, also a ciphertext $s := \Enc{k}{c^d \bmod N}$ by symmetric key encryptions. And she knows a symmetric key $k$.</dd>

  <dt>Verifier Bob</dt>
  <dd>Bob knows the public key $(e, N)$ and the ciphertext $c$, the ciphertext $s$ by symmetric key encryptions. However, he does not know the secret key $d$ corresponding to the public key $(e, N)$ and the symmetric key $k$.</dd>
</dl>

Alice wants to prove the following.

> A preimage $k$ of a hash value $H(k)$ equals to the symmetric key $k$ for decrypting the ciphertext $s$. 

Bob makes sure that the preimage of $H(k)$ is definitely the symmetric key $k$ for decrypting the ciphertext $s$ without Bob knowing the private key $d$ and the symmetric key $k$. And the result of decrypting the ciphertext $s$ is the result of decrypting the ciphertext $c$.
Alice and Bob will run the following cut-and-choose protocol for each ciphertext $c_1, \dots, c_m$ in total $m$ times. For a ciphertext $c_j$ the cut-and-choose is the following.

1. Bob creates $n$ random numbers $r_1, \dots, r_n\; (1 \le r_i \lt N)$ and calculates $\sigma_i := (r_i)^e \bmod N \; (i := 1, \dots, n)$
2. Bob creates $l$ random numbers $\rho_1, \dots, \rho_l\; (1 \le \rho_i \lt N)$ and calculates $\delta_i := c_j \cdot (\rho_i)^e \bmod N \; (i := 1, \dots, l)$
3. Bob chooses a random permutation $\beta := \\{\beta_1, \dots, \beta_{n + l}\\}$ for $\\{\sigma_1, \dots, \sigma_n, \delta_1, \dots, \delta_l\\}$ and sends $\beta$ to Alice. In addition all $\sigma_i$ of $\beta$ is in $F$ and the all $\delta_i$ of $\beta$ is in $R$
4. For $i := 1, \dots, n + l$, Alice
  - creates a random number $k_i$ and a ciphertext $s_i := \Enc{k_i}{(\beta_i)^d \bmod N}$
  - calculates a hash value $h_i: = H(k_i)$ 
5. Alice sends $s_1, \dots, s_{n + l}$ and $h_1, \dots, h_{n + l}$ to Bob
6. Bob sends $r_1, \dots, r_n$ and $F$ to Alice
7. Alice confirms $\beta_i = (r_i)^e \bmod N$ for all $i \in F$. If it fails, Alice will cancel because Bob cheated
8. Alice sends $k_i$ for all $i \in F$ to Bob
9. For all $i \in F$, Bob makes sure that $h_i = H(k_i)$ and $r_i = \Dec{k_i}{s_i}$. If it fails, Bob will cancel

Alice can prove that the ciphertext $s_i$ is the result of decrypting $c_i$ that is encrypted by her ransomware with the symmetric key $k_i$ and $k_i$ is the preimage of the hash value $h_i$ with a high probability.

## Phase 3

In this phase, Bob sends Bitcoin to Alice and Alice publishes the secret key at the same time.

1. Bob makes a transaction $\textrm{Tx.1}$ with the following `scriptPubKey` to send $x$ BTC to Alice and sends the transaction to Bitcoin miners

    ```math
\begin{array}{l}
\texttt{OP_SHA256} \\
h_1 \\
\texttt{OP_EQUAL} \\
\texttt{OP_IF} \\
  \;\;\; \texttt{OP_SHA256} \\
  \;\;\; h_2 \\
  \;\;\; \texttt{OP_EQUALVERIFY} \\
  \;\;\; \vdots \\
  \;\;\; \texttt{OP_SHA256} \\
  \;\;\; h_l \\
  \;\;\; \texttt{OP_EQUALVERIFY} \\
  \;\;\; \mathcal{A} \\
\texttt{OP_ELSE} \\
  \;\;\; \text{block height}\, + 100\\
  \;\;\; \texttt{OP_CHECKLOCKTIMEVERIFY} \\
  \;\;\; \texttt{OP_DROP} \\
  \;\;\; \mathcal{B} \\
\texttt{OP_ENDIF} \\
\texttt{OP_CHECKSIG}
\end{array}
    ```
2. Alice checks the following of the transaction $\textrm{Tx.1}$ on the blockchain. If it fails, Alice will cancel
  - The remittance is $x$ BTC
  - $h_1, \dots, h_l$ are hash values that Alice has sent to Bob in Phase 2
  - $\mathcal{A}$ is the public key that corresponds to her Bitcoin address
3. Alice makes a transaction $\textrm{Tx.2}$ as follows. Its `scriptSig` contains the symmetric key $k_i\; (i \in R)$ and Alice's signature $\mathbb{S}_A$. She sends it to miners

    ```math
\begin{array}{l}
k_1 \\
k_2 \\
\vdots \\
k_l \\
\mathbb{S}_A
\end{array}
    ```
4. If Alice's transaction $\textrm{Tx.2}$ is accepted, the following two will happen at the same time where $(i \in R)$
  - Bob gets $t_i = \Dec{k_i}{s_i} \, / \, \bmod N$ using the symmetric key $k_i$ of the transaction $\textrm{Tx.2}$ on the blockchain
  - Alice gets $x$ BTC since the transaction $\textrm{Tx.2}$ was accepted

First, we consider how `scriptPubKey` of the transaction $\textrm{Tx.1}$ works in (1). In (3) Alice creates the transaction $\textrm{Tx.2}$ which contains the symmetric key $k_i\; (i \in R)$ and Alice's signature $\mathbb{S}_A$. Bitcoin miners run `scriptSig` of the transaction $\mathrm{Tx.2}$ so the stack after run the `scriptSig` of the transaction $\mathrm{Tx.2}$ is as follows.

```math
\SFive{k_1, k_2, \cdots, k_l, \mathbb{S}_A}
```

The transaction $\mathrm{Tx.1}$ `scriptPubKey` is run as follows under this stack.

1. By $\texttt{OP_SHA256}$, calculate a hash value of the top of the stack and push it to the stack $\SFive{H(k_1), k_2, \cdots, k_l, \mathbb{S}_A}$
2. Push $h_1$ to the stack $\SSix{h_1, H(k_1), k_2, \cdots, k_l, \mathbb{S}_A}$
3. By $\texttt{OP_EQUAL}$, compare the first value and the second value of the stack. If they equal push $1$ to the stack, otherwise push $0$. $\SFive{1, k_2, \cdots, k_l, \mathbb{S}_A}$
4. By $\texttt{OP_IF}$, if the top of the satck is $1$, pop and run *then-clause* (from $\texttt{OP_IF}$ to $\texttt{OP_ELSE}$) $\SFour{k_2, \cdots, k_l, \mathbb{S}_A}$
5. By $\texttt{OP_EQUALVERIFY}$, hash values $H(k_2), \dots, H(k_l)$ equal to $h_2, \dots, h_l$. If any one does not equal, it fails $\SOne{\mathbb{S}_A}$
6. Push Alice's public key $\mathcal{A}$ to the stack $\STwo{\mathcal{A}, \mathbb{S}_A}$
7. By $\texttt{OP_CHECKSIG}$, verify a signature on the top of the stack with the second value of the stack as a public key. If the verification will be successful push $1$ to the stack, otherwise push $0$ to the stack $\SOne{1}$

In this way the scripts will be successful.
In addition, by this `scriptPubKey` if miners fail the comparison of the hash value $h_1$, they will run *else-clause* (from $\texttt{OP_ELSE}$ to $\texttt{OP_ENDIF}$). By this else-clause, Bob can withdraw the $x$ BTC after a while even if Alice disappears after (1). Bob may make a transaction $\textrm{Tx.3}$ after the length of the blockchain increases more than 100 than when he has send the transaction $\textrm{Tx.1}$. Bob sends $\textrm{Tx.3}$ that has the following `scriptSig` using Bob's signature $\mathbb{S}_B$ to get back his Bitcoin.

```math
  \begin{array}{l}
  1 \\
  \mathbb{S}_B \\
\end{array}
```

When miners run the transaction $\textrm{Tx.3}$ `scriptSig` the stack is as follows.

```math
  \STwo{1, \mathbb{S}_B}
```

The `scriptPubKey` of the transaction $\textrm{Tx.1}$ will be run under the stack in the following manner.

1. By $\texttt{OP_SHA256}$, calculate a hash value of the top of the stack and push the hash value to the stack $\STwo{H(1), \mathbb{S}_B}$
2. Push $h_1$ to the stack $\SThree{h_1, H(1), \mathbb{S}_B}$
3. By $\texttt{OP_EQUAL}$, compare the first value and the second value of the stack. If they are equal push $1$ to the stack, otherwise push $0$ to the stack $\STwo{0, \mathbb{S}_B}$
4. By $\texttt{OP_IF}$, if the top of the stack is $0$, pop and run the else-clause $\SOne{\mathbb{S}_B}$
5. Push a sum of the length of the blockchain when $\textrm{Tx.1}$ was accepted and $100$ to the stack $\STwo{\textrm{block height} + 100, \mathbb{S}_B}$
6. By $\texttt{OP_CHECKLOCKTIMEVERIFY}$, the script will fail if the length of the current blockchain is less than the top of the stack, otherwise push $1$ to the stack $\STwo{1, \mathbb{S}_B}$
7. By $\texttt{OP_DROPD}$, drop the top of the stack $\SOne{\mathbb{S}_B}$
8. Push Bob's public key $\mathcal{B}$ to the stack $\SOne{\mathbb{S}_B}$
9. By $\texttt{OP_CHECKSIG}$, verify a signature on the top of the stack with the second value of the stack as a public key. If the verification will be successful push $1$ to the stack, otherwise push $0$ to the stack $\SOne{1}$

In this way, Bob will be able to withdraw Bitcoins.

# Conclusion

We will be able to create a fair ransomware using this protocol. If I am forced to say, Alice proves that a ciphertext is the result of encrypting Bob's data by decrypting at least one data for free. If Alice can prove that without decrypting at least one data, it will be considered to be a better protocol.

Thank you for reading this article. Your comments, problem reports and questions are very welcome!

# Acknowledgment

Some members of CTF team [urandom](https://urandom.team/) helped me to fix this article. Some members of DWANGO English Club pointed out mistakes in this article and gave me advices about Engilsh.

# References

[This article](https://bitcoincore.org/en/2016/02/26/zero-knowledge-contingent-payments-announcement/) says *Zero-Knowledge Contingent Payment (ZKCP)* and its application. The ZKCP allows us to exchange a preimage of a hash value and Bitcoins at the same time. It is exactly what we used in the fair ransomeware protocol. [This paper](https://eprint.iacr.org/2016/575.pdf) says about the fair mixing of Bitcoin using ZKCP. If you are interested in ZKCP, you try to read these articles.

- [The first successful Zero-Knowledge Contingent Payment](https://bitcoincore.org/en/2016/02/26/zero-knowledge-contingent-payments-announcement/)
- [TumbleBit: An Untrusted Bitcoin-Compatible Anonymous Payment Hub](https://eprint.iacr.org/2016/575.pdf)
- [Scripts (Bitcoin Wiki)](https://en.bitcoin.it/wiki/Script)

# Contacts

- Twitter: [@\_yyu\_](https://twitter.com/_yyu_)
- Email: yyu@mental.poker
- GitHub: [y-yu](https://github.com/y-yu)
