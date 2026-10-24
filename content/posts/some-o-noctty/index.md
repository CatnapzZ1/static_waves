---
title: "关于O_NOCTTY的一些边角料"
slug: "some-o-noctty"
date: "2026-10-24T23:44:27+08:00"
description: "在Linux上写一个简陋的串口通讯工具时关于O_NOCTTY的一些思考"
categories: ["学习笔记"]
tags: ["C","port","POSIX"]
draft: false
cover:
  image: "cover.png"
  alt: "ATRI"
  relative: true
---

## 什么是controlling terminal？

总的来说，controlling terminal是Unix 内核给一个 session 绑定的一个特殊 TTY 设备。 比如说在一个Terminal Emulator里运行一个shell:

```text
Kitty
  │
  │ 申请创建 PTY
  ▼
/dev/pts/3
  ├── bash
  ├── vim
  ├── ffmpeg
  └── ./hello
```

这个bash所在session的controlling terminal通常就是/dev/pts/3，它主要负责把TTY产生的终端事件和一个session 中的进程关联起来。

## 为什么USB串口也能成为 controlling terminal

插入一个USB转串口设备时：

```text
USB 转串口芯片
  │
  ▼
Linux USB serial driver
  │
  ▼
TTY subsystem
  │
  ▼
/dev/ttyUSB0
```

这个时候Linux 内核向用户空间暴露的是一个TTY对象。在内核看来，只要它是一个TTY，理论上就可以成为controlling terminal。 假设一个程序 open("/dev/ttyUSB0", O_RDWR) （没有指定O_NOCTTY）又恰好这个进程是session leader并且当前session没有controlling terminal又恰好打开的对象是一个可以作为ontrolling terminal的TTY等特定条件下，内核就可能记录session X 的 controlling tty = ttyUSB0，于是这个 TTY 上发生的一些终端语义，就可能作用于这个 session。

## O_NOCTTY控制谁

O_NOCTTY 控制的是：调用 open() 的这个进程 / 它所属的 session，是否把被打开的 TTY 当作 controlling terminal。

```c
#include <fcntl.h>

int fd = open("/dev/ttyUSB0", O_RDWR | O_NOCTTY);
```

## 什么场景下更应该关注

普通场景下程序继承Terminal Emulator的controlling terminal,一个session通常不会因为后来随便open()一个/dev/ttyUSB0,就直接把controlling terminal换过去，所以很多时候表面上也不会出问题。 但如果程序进行了daemon化，条件满足的话串口设备就有可能莫名其妙变成这个session的控制终端。 O_NOCTTY作为open()的调用选项，它阻止的是“正在执行open的进程所在session”因为这次打开TTY，而获得“被打开TTY”作为 controlling terminal。
