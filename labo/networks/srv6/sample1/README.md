# sample1

- 以下のブログのやつをそのまま試してみる
  - https://blog.bobuhiro11.net/2021/01-17-srv6linux.html

```
$ sudo ./setup.sh
```

## ping の dump 結果

```
$ tshark -r /tmp/srv6-demo.pcap | grep "(ping) request"
# Plain ping6
   17   2.897941    fc00:a::1 → fc00:d::2    ICMPv6 118 Echo (ping) request id=0x5f9e, seq=1, hop limit=63
# SRv6 Encap ping6
   21   5.915771    fc00:a::1 → fc00:d::2    ICMPv6 182 Echo (ping) request id=0xf87d, seq=1, hop limit=64
# SRv6 Inline ping6
   27   8.934192    fc00:a::1 → fc00:d::2    ICMPv6 158 Echo (ping) request id=0x9ac9, seq=1, hop limit=63
```

```
# Plain ping6
# ベースライン。素直にH1 fc00:a::1からH2 fc00:d::2へ送られる
$ tshark -r /tmp/srv6-demo.pcap -Y "frame.number == 17 or frame.number == 21 or frame.number == 27" -V
Frame 17: 118 bytes on wire (944 bits), 118 bytes captured (944 bits)
    Encapsulation type: Ethernet (1)
    Arrival Time: Nov 20, 2022 23:16:24.055893000 JST
    [Time shift for this packet: 0.000000000 seconds]
    Epoch Time: 1668953784.055893000 seconds
    [Time delta from previous captured frame: 0.000007000 seconds]
    [Time delta from previous displayed frame: 0.000000000 seconds]
    [Time since reference or first frame: 2.897941000 seconds]
    Frame Number: 17
    Frame Length: 118 bytes (944 bits)
    Capture Length: 118 bytes (944 bits)
    [Frame is marked: False]
    [Frame is ignored: False]
    [Protocols in frame: eth:ethertype:ipv6:icmpv6:data]
Ethernet II, Src: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be), Dst: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
    Destination: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
        Address: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
        .... ..1. .... .... .... .... = LG bit: Locally administered address (this is NOT the factory default)
        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
    Source: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be)
        Address: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be)
        .... ..1. .... .... .... .... = LG bit: Locally administered address (this is NOT the factory default)
        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
    Type: IPv6 (0x86dd)
Internet Protocol Version 6, Src: fc00:a::1, Dst: fc00:d::2
    0110 .... = Version: 6
    .... 0000 0000 .... .... .... .... .... = Traffic Class: 0x00 (DSCP: CS0, ECN: Not-ECT)
        .... 0000 00.. .... .... .... .... .... = Differentiated Services Codepoint: Default (0)
        .... .... ..00 .... .... .... .... .... = Explicit Congestion Notification: Not ECN-Capable Transport (0)
    .... 0110 1011 1100 0000 1001 = Flow Label: 0x6bc09
    Payload Length: 64
    Next Header: ICMPv6 (58)
    Hop Limit: 63
    Source Address: fc00:a::1
    Destination Address: fc00:d::2
Internet Control Message Protocol v6
    Type: Echo (ping) request (128)
    Code: 0
    Checksum: 0x3e83 [correct]
    [Checksum Status: Good]
    Identifier: 0x5f9e
    Sequence: 1
    Data (56 bytes)

0000  b8 36 7a 63 00 00 00 00 f7 d9 00 00 00 00 00 00   .6zc............
0010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f   ................
0020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f    !"#$%&'()*+,-./
0030  30 31 32 33 34 35 36 37                           01234567
        Data: b8367a6300000000f7d9000000000000101112131415161718191a1b1c1d1e1f20212223…
        [Length: 56]

# SRv6 Encap ping6
Frame 21: 182 bytes on wire (1456 bits), 182 bytes captured (1456 bits)
    Encapsulation type: Ethernet (1)
    Arrival Time: Nov 20, 2022 23:16:27.073723000 JST
    [Time shift for this packet: 0.000000000 seconds]
    Epoch Time: 1668953787.073723000 seconds
    [Time delta from previous captured frame: 3.017661000 seconds]
    [Time delta from previous displayed frame: 3.017830000 seconds]
    [Time since reference or first frame: 5.915771000 seconds]
    Frame Number: 21
    Frame Length: 182 bytes (1456 bits)
    Capture Length: 182 bytes (1456 bits)
    [Frame is marked: False]
    [Frame is ignored: False]
    [Protocols in frame: eth:ethertype:ipv6:ipv6.routing:ipv6:icmpv6:data]
Ethernet II, Src: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be), Dst: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
    Destination: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
        Address: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
        .... ..1. .... .... .... .... = LG bit: Locally administered address (this is NOT the factory default)
        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
    Source: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be)
        Address: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be)
        .... ..1. .... .... .... .... = LG bit: Locally administered address (this is NOT the factory default)
        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
    Type: IPv6 (0x86dd)
Internet Protocol Version 6, Src: fc00:b::1, Dst: fc00:e::2
    0110 .... = Version: 6
    .... 0000 0000 .... .... .... .... .... = Traffic Class: 0x00 (DSCP: CS0, ECN: Not-ECT)
        .... 0000 00.. .... .... .... .... .... = Differentiated Services Codepoint: Default (0)
        .... .... ..00 .... .... .... .... .... = Explicit Congestion Notification: Not ECN-Capable Transport (0)
    .... 0110 1011 1100 0000 1001 = Flow Label: 0x6bc09
    Payload Length: 128
    Next Header: Routing Header for IPv6 (43)
    Hop Limit: 63
    Source Address: fc00:b::1
    Destination Address: fc00:e::2
    Routing Header for IPv6 (Segment Routing)
        Next Header: IPv6 (41)
        Length: 2
        [Length: 24 bytes]
        Type: Segment Routing (4)
        Segments Left: 0
        Last Entry: 0
        Flags: 0x00
        Tag: 0000
        Address[0]: fc00:e::2
Internet Protocol Version 6, Src: fc00:a::1, Dst: fc00:d::2
    0110 .... = Version: 6
    .... 0000 0000 .... .... .... .... .... = Traffic Class: 0x00 (DSCP: CS0, ECN: Not-ECT)
        .... 0000 00.. .... .... .... .... .... = Differentiated Services Codepoint: Default (0)
        .... .... ..00 .... .... .... .... .... = Explicit Congestion Notification: Not ECN-Capable Transport (0)
    .... 0110 1011 1100 0000 1001 = Flow Label: 0x6bc09
    Payload Length: 64
    Next Header: ICMPv6 (58)
    Hop Limit: 64
    Source Address: fc00:a::1
    Destination Address: fc00:d::2
Internet Control Message Protocol v6
    Type: Echo (ping) request (128)
    Code: 0
    Checksum: 0xcb5d [correct]
    [Checksum Status: Good]
    Identifier: 0xf87d
    Sequence: 1
    Data (56 bytes)

0000  bb 36 7a 63 00 00 00 00 ce 1f 01 00 00 00 00 00   .6zc............
0010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f   ................
0020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f    !"#$%&'()*+,-./
0030  30 31 32 33 34 35 36 37                           01234567
        Data: bb367a6300000000ce1f010000000000101112131415161718191a1b1c1d1e1f20212223…
        [Length: 56]

# SRv6 Inline ping6
Frame 27: 158 bytes on wire (1264 bits), 158 bytes captured (1264 bits)
    Encapsulation type: Ethernet (1)
    Arrival Time: Nov 20, 2022 23:16:30.092144000 JST
    [Time shift for this packet: 0.000000000 seconds]
    Epoch Time: 1668953790.092144000 seconds
    [Time delta from previous captured frame: 0.813652000 seconds]
    [Time delta from previous displayed frame: 3.018421000 seconds]
    [Time since reference or first frame: 8.934192000 seconds]
    Frame Number: 27
    Frame Length: 158 bytes (1264 bits)
    Capture Length: 158 bytes (1264 bits)
    [Frame is marked: False]
    [Frame is ignored: False]
    [Protocols in frame: eth:ethertype:ipv6:ipv6.routing:icmpv6:data]
Ethernet II, Src: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be), Dst: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
    Destination: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
        Address: 8e:33:22:1c:92:4b (8e:33:22:1c:92:4b)
        .... ..1. .... .... .... .... = LG bit: Locally administered address (this is NOT the factory default)
        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
    Source: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be)
        Address: 2a:8c:05:f5:19:be (2a:8c:05:f5:19:be)
        .... ..1. .... .... .... .... = LG bit: Locally administered address (this is NOT the factory default)
        .... ...0 .... .... .... .... = IG bit: Individual address (unicast)
    Type: IPv6 (0x86dd)
Internet Protocol Version 6, Src: fc00:a::1, Dst: fc00:e::2
    0110 .... = Version: 6
    .... 0000 0000 .... .... .... .... .... = Traffic Class: 0x00 (DSCP: CS0, ECN: Not-ECT)
        .... 0000 00.. .... .... .... .... .... = Differentiated Services Codepoint: Default (0)
        .... .... ..00 .... .... .... .... .... = Explicit Congestion Notification: Not ECN-Capable Transport (0)
    .... 0110 1011 1100 0000 1001 = Flow Label: 0x6bc09
    Payload Length: 104
    Next Header: Routing Header for IPv6 (43)
    Hop Limit: 63
    Source Address: fc00:a::1
    Destination Address: fc00:e::2
    Routing Header for IPv6 (Segment Routing)
        Next Header: ICMPv6 (58)
        Length: 4
        [Length: 40 bytes]
        Type: Segment Routing (4)
        Segments Left: 1
        Last Entry: 1
        Flags: 0x00
        Tag: 0000
        Address[0]: fc00:d::2
        Address[1]: fc00:e::2
Internet Control Message Protocol v6
    Type: Echo (ping) request (128)
    Code: 0
    Checksum: 0x26ca [correct]
    [Checksum Status: Good]
    Identifier: 0x9ac9
    Sequence: 1
    Data (56 bytes)

0000  be 36 7a 63 00 00 00 00 cd 67 01 00 00 00 00 00   .6zc.....g......
0010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f   ................
0020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f    !"#$%&'()*+,-./
0030  30 31 32 33 34 35 36 37                           01234567
        Data: be367a6300000000cd67010000000000101112131415161718191a1b1c1d1e1f20212223…
        [Length: 56]
```
