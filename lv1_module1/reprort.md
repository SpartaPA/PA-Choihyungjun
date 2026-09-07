# 모듈 과제 1

## 0. 전제 — 로봇 구성과 센서별 데이터량

지시문에 주어진 센서와 통신 장치들을 먼저 숫자로 정리. 이후 모든 배치 판단은 이 표의 지연 예산과 데이터량을 근거로 함

| 장치 | 갱신 주기 | 1회 데이터 (가정) | 데이터율 | 비고 |
| :--- | :--- | :--- | :--- | :--- |
| **바퀴 엔코더** | 2 kHz (0.5 ms) | 2륜 × 4 B 카운터 = 8 B | 16 KB/s | 모터 제어 루프의 피드백 |
| **IMU** | 400 Hz (2.5 ms) | 가속도 3축 + 각속도 3축 × 4 B + 타임스탬프 8 B = 32 B | 12.8 KB/s | 자세·오도메트리 융합 |
| **2D 라이다** | 15 Hz (66.7 ms) | 360 점 × (거리 4 B + 세기 4 B) = 2,880 B | 43.2 KB/s ≈ 0.35 Mbps | 장애물 감지 |
| **RGB 카메라** | 60 fps (16.7 ms) | 1280 × 720 × 3 B = 2,764,800 B ≈ 2.76 MB | 165.9 MB/s ≈ 1,327 Mbps | 보행자 인식 (원시 영상 기준) |
| **LTE 모듈** | — | — | 업/다운링크 95~100 Mbps | 왕복 지연(RTT) 1~5 ms |

> **주행 및 제동 조건**  
> 배달 로봇의 주행 속도는 보도 주행 규정에 맞춰 $v = 1.5\text{ m/s}$, 감속도 $a = 2\text{ m/s}^2$ 로 가정
> 이 값으로 제동 거리는 $v^2 / 2a = 0.56\text{ m}$ 이고, **100 ms 반응 지연마다 0.15 m 씩 더 진행**

---

## 1. 배달 로봇의 연산 분담과 실시간성 설계

배달 로봇에 다음이 실려 있다고 가정 — 2D 라이다(15Hz), RGB 카메라(60fps·720p), IMU(400Hz), 바퀴 엔코더(2kHz), 모터 드라이버, LTE 모듈(핑 1~5ms, 업/다운로드 95~100Mbps).

### 1. 이 로봇이 하는 작업 여섯 가지(모터 속도 제어, 장애물 감지, 보행자 인식, 지도 기반 경로 계획, 배달 완료 사진 업로드, 운행 로그 집계)를 임베디드 / Edge AI / 클라우드 중 어디서 처리할지 표로 배치하고, 지연 예산과 데이터 전송량을 근거로 각각 이유를 쓰세요(1강).

| 작업 | 계층 | 지연 예산 | 데이터량 | 근거 |
| :--- | :--- | :--- | :--- | :--- |
| 모터 속도 제어 | 임베디드 | ≤ 1~2 ms | 엔코더 16 + IMU 12.8 KB/s | 갱신 주기가 0.5 ms(엔코더)·2.5 ms(IMU)로 매우 짧고 연산량이 작아 임베디드로 처리 |
| 장애물 감지 | Edge AI | ~50 ms | 라이다 43.2 KB/s | 대역폭은 여유(0.35 Mbps)지만 제동에 직결되는 안전 기능을 네트워크 끊김,혼잡에 의존시킬 수 없어 로컬에서 결정, Egde AI 사용 |
| 보행자 인식 | Edge AI | ~50 ms | 카메라 원시 165.9 MB/s | 원시 영상 1,327 Mbps > LTE 100 Mbps라 클라우드 전송이 불가능해 Edge에서 인식 후 결과만 전송 |
| 지도 기반 경로 계획 | 클라우드 | 초 단위 | 소량(경로·지도) | 지연돼도 주행에 지장 없고 대규모 지도·연산은 클라우드가 유리 |
| 배달 완료 사진 업로드 | 클라우드 | 초~분 단위 | 사진 배치 | 실시간성이 필요 없고 지연을 허용 |
| 운행 로그 집계 | 클라우드 | 분 단위 | 로그 배치 | 실시간성이 필요 없어 모아서 일괄 전송 |

### 2. 카메라 원시 영상을 클라우드로 계속 보내면 초당 몇 MB 인지 계산하고, LTE 대역폭과 비교해 그 설계가 왜 성립하지 않는지 수치로 보이세요.
- 2.76MB $\times$ 60 = 165.9 MB/s ≈ 1,327 Mbps
- LTE 업링크는 95~100Mbps이므로 필요 대역폭이 가용 대역폭의 약 13배를 초과하게 됨 -> 원시 영상을 실시간으로 클라우드로 보내는 설계는 성립하지 않고 Edge AI에서 인식 후 결과만 전송하거나 데이터를 압축하여 데이터율을 낮춰야 함.


### 3. 같은 작업들을 인지 → 판단 → 제어 계층에 매핑하고, 계층별 갱신 주기를 적어 멀티레이트 데이터 흐름을 그림이나 표로 정리하세요(2강).

| 계층 | 작업 | 갱신 주기 |
| :--- | :--- | :--- |
| 인지 | 보행자 인식 | 16.7 ms (60 fps) |
| 인지 | 장애물 감지 | 66.7 ms (15 Hz) |
| 판단 | 지도 기반 경로 계획 | 초 단위 |
| 제어 | 모터 속도 제어 | 0.5 ms (2 kHz) |

![멀티레이트_데이터_흐름](/lv1_module1/images/멀티레이트%20데이터%20흐름.png)


### 4. 여섯 작업을 Hard / Firm / Soft 실시간으로 분류하고, Hard 로 분류한 작업이 마감을 놓치면 어떤 물리적 결과가 생기는지 한 줄씩 쓰세요.

- Hard : 모터 속도 제어
- Firm : 장애물 감지, 보행자 인식
- Soft : 지도 기반 경로 계획, 배달 완료 사진 업로드, 운행 로그 집계

- Hard로 분류한 작업이 마감을 놓치면 제어 루프가 피드백을 시간안에 못 받아 제동 명령이 늦어져 로봇이 궤적을 벗어나거나 장애물과 충돌한게 됨.


### 5. 주기·지연·지터를 이 로봇의 예로 각각 한 문장씩 구분해 설명하세요.

| 장치 | 주기 | 지연 | 지터 |
| --- | --- | --- | --- |
| 바퀴 엔코더 | 0.5 ms마다 카운터를 읽어서 모터 루프에 피드백 | 엔코더 값이 모터에 반영되는 시간 | 0.5 ms 간격이 흔들리면 제어 주기가 불안정해짐 |
| IMU | 2.5 ms마다 가속도, 각속도 측정 | 측정 시점부터 자세가 반영되기까지 걸리는 시간 | 측정 간격이 2.5 ms가 아닌 2~3 ms로 흔들리며 위치 추정 오차 증가 |
| 2D 라이다 | 66.7 ms마다 장애물 스캔 | 장애물 감지 시점부터 모터가 감속하는데 걸리는 시간 | 스캔 주기가 흔들리며 장애물의 위치, 속도 갱신이 불규칙해짐 |
---

## 2. 원격 접속(SSH)과 센서 장치 경로 고정

### 1. localhost로 접속

```shell
pa33@pa33-Legion-Pro-5-16IAX10:~$ ssh pa33@localhost
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-138-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

Expanded Security Maintenance for Applications is not enabled.

189 updates can be applied immediately.
To see these additional updates run: apt list --upgradable

143 additional security updates can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm

New release '24.04.4 LTS' available.
Run 'do-release-upgrade' to upgrade to it.

Last login: Tue Aug 25 14:14:47 2026 from 127.0.0.1
pa33@pa33-Legion-Pro-5-16IAX10:~$ wh
pa33     tty2         2026-08-25 00:09 (tty2)
pa33     pts/3        2026-08-25 14:14 (127.0.0.1)
pa33     pts/4        2026-08-25 14:15 (127.0.0.1)
pa33@pa33-Legion-Pro-5-16IAX10:~$ echo $SSH_CONNECTION
127.0.0.1 44232 127.0.0.1 22

```

### 2. 공개키 등록 / 
- 서버에 등록되는 것은 공개키(`~/.ssh/authorized_keys`)이고, 개인키는 클라이언트에만 남아 전송되지 않는다.
- 공개키로는 서명 검증만 가능하고 이 값으로 개인키를 역산할 수 없어, 공개키가 노출돼도 안전


### 3. 원격 단일 명령 실행과 scp 전송 출력
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~$ ssh pa33@localhost 'uname -a'
Linux pa33-Legion-Pro-5-16IAX10 6.8.0-138-generic #138~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Fri Aug  7 13:43:15 UTC  x86_64 x86_64 x86_64 GNU/Linux
```

- scp 전송 출력
```shell
# 로컬
# 전송 파일 생성
pa33@pa33-Legion-Pro-5-16IAX10:~$ echo "headless test" > test.txt

# 전송
pa33@pa33-Legion-Pro-5-16IAX10:~$ scp test.txt pa33@localhost:~
test.txt                                                                                                   100%   14     1.8KB/s   00:00 

# 원격
pa33@pa33-Legion-Pro-5-16IAX10:~$ cat ~/test.txt
headless test
```  



### 4. 두 장치를 구분한 속성

- lidar와 imu가 임의로 생성한 img여서 차이가 명확하지 않음 -> lidar는 16M, imu는 24M로 수정 

```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ losetup -a
/dev/loop1: []: (/var/lib/snapd/snaps/core22_1612.snap)
/dev/loop17: []: (/home/pa33/fake_sensors/imu.img)
/dev/loop8: []: (/var/lib/snapd/snaps/gtk-common-themes_1535.snap)
/dev/loop15: []: (/var/lib/snapd/snaps/snapd-desktop-integration_391.snap)
/dev/loop6: []: (/var/lib/snapd/snaps/gnome-42-2204_263.snap)
/dev/loop13: []: (/var/lib/snapd/snaps/snapd_27710.snap)
/dev/loop4: []: (/var/lib/snapd/snaps/firefox_4848.snap)
/dev/loop11: []: (/var/lib/snapd/snaps/snap-store_1216.snap)
/dev/loop2: []: (/var/lib/snapd/snapsㅗ/core24_1643.snap)
/dev/loop0: []: (/var/lib/snapd/snaps/bare_5.snap)
/dev/loop9: []: (/var/lib/snapd/snaps/mesa-2404_1839.snap)
/dev/loop16: []: (/home/pa33/fake_sensors/lidar.img)
/dev/loop7: []: (/var/lib/snapd/snaps/gnome-46-2404_164.snap)
/dev/loop14: []: (/var/lib/snapd/snaps/snapd-desktop-integration_178.snap)
/dev/loop5: []: (/var/lib/snapd/snaps/gnome-42-2204_176.snap)
/dev/loop12: []: (/var/lib/snapd/snaps/snapd_27591.snap)
/dev/loop3: []: (/var/lib/snapd/snaps/core22_2437.snap)
/dev/loop10: []: (/var/lib/snapd/snaps/snap-store_1113.snap)
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ diff -u <(udevadm info -a /dev/loop17) <(udevadm info -a /dev/loop16)
--- /dev/fd/63	2026-09-06 09:47:38.807321078 +0900
+++ /dev/fd/62	2026-09-06 09:47:38.807321078 +0900
@@ -5,14 +5,14 @@
 A rule to match, can be composed by the attributes of the device
 and the attributes from one single parent device.
 
-  looking at device '/devices/virtual/block/loop17':
-    KERNEL=="loop17"
+  looking at device '/devices/virtual/block/loop16':
+    KERNEL=="loop16"
     SUBSYSTEM=="block"
     DRIVER==""
     ATTR{alignment_offset}=="0"
     ATTR{capability}=="0"
     ATTR{discard_alignment}=="0"
-    ATTR{diskseq}=="39"
+    ATTR{diskseq}=="37"
     ATTR{events}=="media_change"
     ATTR{events_async}==""
     ATTR{events_poll_msecs}=="-1"
@@ -84,8 +84,8 @@
     ATTR{range}=="1"
     ATTR{removable}=="0"
     ATTR{ro}=="0"
-    ATTR{size}=="49152"
-    ATTR{stat}=="      68        0     1344        0        0        0        0        0        0        0        0        0        0        0        0        0        0"
+    ATTR{size}=="32768"
+    ATTR{stat}=="      79        0     1372        2        0        0        0        0        0        1        2        0        0        0        0        0        0"
     ATTR{trace/act_mask}=="disabled"
     ATTR{trace/enable}=="0"
     ATTR{trace/end_lba}=="disabled"
```

- 구분 속성: ATTR{size} — 라이다 `32768`(16M) / IMU `49152`(24M)

### 5. 작성한 udev 규칙 2개 + 규칙 키 설명표
- udev 규칙 

```shell
# 99-robot-sensor.rules

# Lidar
SUBSYSTEM=="block", KERNEL=="loop*", ATTRS{size}=="32768", SYMLINK+="robot_lidar", MODE="0666"

# imu
SUBSYSTEM=="block", KERNEL=="loop*", ATTRS{size}=="49152", SYMLINK+="robot_imu", MODE="0666"
```

- 규칙 키 설명

| 키 | 의미 |
| :--- | :--- |
| `SUBSYSTEM` | 장치가 속한 서브시스템 (block, tty 등) |
| `KERNEL` | 커널이 붙인 장치 이름 패턴 (`loop*`) |
| `ATTR{...}` | 매칭 대상 장치 자신의 sysfs 속성 |
| `ATTRS{...}` | 대상 장치 또는 상위(부모) 장치의 sysfs 속성 (부모까지 거슬러 탐색) |
| `SYMLINK+=` | `/dev` 아래에 고정 심볼릭 링크 추가 |
| `MODE` | 장치 파일 접근 권한 |
| `GROUP` | 장치 파일 소유 그룹 |

- 연산자 차이

| 연산자 | 뜻 |
| :--- | :--- |
| `==` | 조건 비교(매칭). 이 규칙을 장치에 적용할지 판단 |
| `=` | 값 대입(덮어쓰기). `MODE=`, `GROUP=` 등 |
| `+=` | 기존 값에 추가. `SYMLINK+=` 는 링크를 덧붙임 |


### 6. 순서 바꿔 재연결 후 ls -l /dev/robot_* 결과
```shell
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup --show lidar.img
losetup: lidar.img: failed to use device: No such device
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -f --show lidar.img
/dev/loop18
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -f --show imu.img 
/dev/loop19
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ ls -l /dev/robot_*
lrwxrwxrwx 1 root root 6 Aug 28 10:04 /dev/robot_imu -> loop19
lrwxrwxrwx 1 root root 6 Aug 28 10:04 /dev/robot_lidar -> loop18

# 순서 바꿔 재연결
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -d /dev/loop18 /dev/loop19
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -f --show imu.img 
/dev/loop18
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ sudo losetup -f --show lidar.img
/dev/loop19
pa33@pa33-Legion-Pro-5-16IAX10:~/fake_sensors$ ls -l /dev/robot_*
lrwxrwxrwx 1 root root 6 Aug 28 10:05 /dev/robot_imu -> loop18
lrwxrwxrwx 1 root root 6 Aug 28 10:05 /dev/robot_lidar -> loop19

```

### 7. 실제 USB 센서용 규칙 초안과 구분 근거
```shell
# Lidar : idVendor 10c4 / idProduct ea60
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="robot_lidar", MODE="0666"

# IMU : idVendor 10c4 / idProduct ea70
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea70", SYMLINK+="robot_imu", MODE="0666"
```

- loop 장치와 달리 USB 시리얼은 `SUBSYSTEM=="tty"`, 구분 키는 `ATTRS{idVendor}`·`ATTRS{idProduct}` 로 바뀐다.
- idVendor(10c4)가 같아도 idProduct가 `ea60`/`ea70` 로 달라 idProduct 로 구분한다.
- 만약 idProduct까지 같은 동일 모델 2대라면 제조 시리얼인 `ATTRS{serial}` 로 구분한다.



## 3. 팀 저장소 협업 — 브랜치·충돌 해결·PR 리뷰
### 1. 저장소 URL : https://github.com/chj1319/Git_pratice / PR URL : https://github.com/chj1319/Git_pratice/pull/1

### 2. PR 리뷰 코멘트와 반영 커밋
![PR_comment&review](/lv1_module1/images/PR_comment_riview.png)

### 3. 충돌이 난 파일과 줄

![git_conflict](/lv1_module1/images/git_conflict.png)

- "<<<<"(start marker)   : 기존 브랜치에서 작업한 내용
- "===="(separator)      : 두 브랜치의 변경 사항을 나누는 기준선 
- ">>>>"(end marker)     : 병합하려는 브랜치에 변경 사항

### 4. merge 방식 이력 그래프 / rebase 방식 이력 그래프

- merge 커밋 이력
```shell
| *   2cfae0a (origin/feature/udev-rules) Merge branch 'main' into feature/udev-rules
| |\  
| |/  
|/|   
* |   f2ba94f Merge pull request #2 from chj1319/feature/compute-layout
|\ \  
| * | 22d477a (origin/feature/compute-layout) fix : 3, 5 항목 추가
| * | 00f4480 fix : 연산 분담 설계 문서 추가
| | * fea353a (feature/udev-rules) fix  : 문제2 규칙 파일
| |/  
|/|   
* | 247cfb5 Merge pull request #1 from chj1319/feature/compute-layout
|\| 
| * dc17d10 fix : 배달로봇 사양 추가
|/  
* 2184a84 Add initial README.md with project title
```

- rebase 커밋 이력
```shell
* 1313a4b (HEAD -> feat-rebase, other, main) other: main 진행
* 71e6829 (feat-merge) base
*   87187c9 (origin/main) Merge pull request #3 from chj1319/feature/udev-rules
```


- merge 방식: 두 브랜치가 갈라졌다 만나는 지점마다  merge commit이 생겨 이력이 다이아몬드 모양으로 남게 됨. 실제 작업 순서와 분기 이력이 그대로 보존
- rebase 방식: 내 커밋을 main 최신 위로 옮겨 붙여 merge commit 없이 한 줄로 정리. 이력은 깔끔하지만 커밋 해시가 새로 바뀜.


### 5. 언제 merge, 언제 rebase를 사용할지
- merge   : 공유 브랜치, 협업 이력을 그대로 남겨야하는 경우
- rebase  : 아직 push 하지 않은 내 로컬 브랜치를 최신화하거나 PR 전 이력을 정리하는 경우 / 이미 push해 남이 받은 커밋은 rebase 금지