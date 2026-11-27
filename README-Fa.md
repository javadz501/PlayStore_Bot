# PlayDL

PlayDL یک ربات تلگرام برای دانلود برنامه از Google Play است. کاربر لینک برنامه را می‌فرستد، ربات برنامه را دانلود می‌کند، اگر فایل‌ها split باشند آن‌ها را به یک APK قابل نصب تبدیل می‌کند و فایل نهایی را در تلگرام برای کاربر می‌فرستد.

این پروژه با Python 3.13 و aiogram 3.28.x ساخته شده

English guide: [README.md](README.md)

## امکانات

- استخراج package name از لینک
- دانلود برنامه با چند backend مختلف
- تبدیل `.apks` یا split APKها به یک `.apk` معمولی
- ارسال APK از سه مسیر:
  - **تلگرام** — آپلود مستقیم (برای فایل بزرگ‌تر از ۵۰ مگابایت نیاز به Local Bot API دارد).
  - **NixFile** — آپلود به `panel.nixfile.com` با Selenium و گرفتن لینک.
  - **روبیکا** — ارسال به هر `@username` از حساب روبیکای ربات با آپلودر چند-تکه موازی و wrap داخل zip (روبیکا پسوند `.apk` را قبول نمی‌کند).
- ذخیره وضعیت jobها در MongoDB

## پیش‌نیازها

- Python 3.13
- MongoDB
- Java 17+
- Telegram Bot API local server
- یکی از دانلودرهای Google Play:
  - پیشنهاد اصلی برای چندمعماری: [`gplaydl 4.x`](https://pypi.org/project/gplaydl/)
  - جایگزین برای حالت تک‌معماری: [`alltechdev/gplay-apk-downloader`](https://github.com/alltechdev/gplay-apk-downloader)
  - جایگزین: [`apkeep`](https://github.com/EFForg/apkeep)
- [`APKEditor.jar`](https://github.com/REAndroid/APKEditor/releases) برای merge کردن split APKها

اگر `AUTO_INSTALL_TOOLS=true` باشد، در حالت چندمعماری، `gplaydl 4.x` نصب یا به‌روزرسانی می‌شود. حالت تک‌معماری همچنان امکان استفاده از alltech-gplay را دارد. ابزارهای APKEditor و signer نیز در صورت نیاز دریافت می‌شوند. سرویس‌ها و پکیج‌های سیستمی مثل Java، MongoDB، Telegram Bot API server، git و Rust خودکار نصب نمی‌شوند.

## نصب

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
python App.main
```

در Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## نصب Java

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y openjdk-17-jre-headless
java -version
```

اگر JDK کامل خواستی:

```bash
sudo apt install -y openjdk-17-jdk
```

CentOS/RHEL/Rocky:

```bash
sudo dnf install -y java-17-openjdk
java -version
```

## دریافت APKEditor

آخرین فایل `APKEditor-*.jar` را از این صفحه بگیر:

https://github.com/REAndroid/APKEditor/releases

بعد داخل این مسیر بگذار:

```text
tools/APKEditor.jar
```

یا مسیرش را در `.env` تنظیم کن:

```env
APKEDITOR_JAR=/opt/apkeditor/APKEditor.jar
```

## تنظیمات اصلی

فایل `.env` را ویرایش کن:

```env
BOT_TOKEN=123456:CHANGE_ME

TELEGRAM_API_BASE_URL=http://127.0.0.1:8081
TELEGRAM_API_IS_LOCAL=true

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=playdl

AUTO_INSTALL_TOOLS=true
TOOLS_DIR=tools
DOWNLOAD_DIR=storage/downloads
MAX_PARALLEL_JOBS=2
```

## تنظیم دانلودر

### alltech gplay (فقط حالت تک‌معماری)

این Backend را فقط با `PLAY_ARCH_MODE=single` استفاده کن. پروفایل‌های لازم برای چهار معماری را ارائه نمی‌کند.

```env
PLAY_DOWNLOADER_BACKEND=alltech-gplay
ALLTECH_GPLAY_PATH=tools/gplay-apk-downloader/gplay
ALLTECH_AUTO_AUTH=true
ALLTECH_AUTH_FILE=~/.gplay-auth.json
PLAY_ARCH=arm64
MERGE_SPLITS=true
```

اگر `AUTO_INSTALL_TOOLS=true` باشد، ربات این repo را داخل `tools/gplay-apk-downloader` clone می‌کند. اگر `ALLTECH_AUTO_AUTH=true` باشد، وقتی `~/.gplay-auth.json` وجود نداشته باشد یک بار `gplay auth` را اجرا می‌کند.

### پیشنهاد اصلی: gplaydl 4.x (چهار معماری)

`gplaydl 4.x` از ARM64، ARMv7، x86_64 و x86 پشتیبانی می‌کند. در حالت `PLAY_ARCH_MODE=all`، ربات هر معماری را جداگانه دانلود و تبدیل می‌کند و APKهای امضاشده را داخل یک ZIP قرار می‌دهد.

```env
PLAY_DOWNLOADER_BACKEND=gplaydl
PLAY_ARCH_MODE=all
GPLAYDL_API_KEY=
```

کلید API اختیاری است؛ اگر runtime را یک‌بار با دستور `gplaydl link` جفت کرده باشی، نیازی به آن نیست. در Docker این دستور را اجرا کن: `docker compose -f Docker/docker-compose.yml exec bot gplaydl link`. Volume فعلی `/root` تنظیمات را نگه می‌دارد. راه دیگر، قراردادن `GPLAYDL_API_KEY` در محیط runtime یا فایل `.env` است؛ کلید را commit نکن.

برای جفت‌سازی اولیه از برنامه gplaydl Authenticator و یک حساب Google جداگانه استفاده کن. Google ممکن است حساب‌های استفاده‌شده در کلاینت‌های غیررسمی را محدود کند؛ از حساب اصلی استفاده نکن.

### apkeep

اگر از apkeep استفاده می‌کنی و اکانت/توکن Google Play داری:

```env
PLAY_DOWNLOADER_BACKEND=apkeep
APKEEP_SOURCE=google-play
APKEEP_EMAIL=you@example.com
APKEEP_TOKEN=your_aas_token
```

اگر نصب خودکار فعال باشد و `apkeep` پیدا نشود، ربات با `cargo install apkeep` نصبش می‌کند. برای این حالت Rust/Cargo باید از قبل نصب باشد.

### دستور دلخواه

اگر دانلودر اختصاصی خودت را داری:

```env
PLAY_DOWNLOADER_BACKEND=custom
PLAY_DOWNLOADER_CMD=apkeep -a "{package}" "{output_dir}"
APKS_TO_APK_CMD=java -jar tools/APKEditor.jar m -i "{input}" -o "{output}"
```

متغیرهای قابل استفاده:

- `{url}`: لینک کامل Google Play
- `{package}`: نام پکیج، مثل `org.telegram.messenger`
- `{output_dir}`: پوشه دانلود همان job
- `{arch}`: معماری انتخاب شده، مثل `arm64`

## تنظیم آپلودر

### NixFile
در nixfile.com اکانت بساز و `NIXFILE_USERNAME` و `NIXFILE_PASS` را در `.env` بگذار. ربات بار اول لاگین می‌کند و session را برای دفعات بعد ذخیره می‌کند.

### روبیکا
کانال روبیکا فایل APK را از حساب روبیکای ربات برای هر `@username` می‌فرستد. احراز با فایل session از قبل ساخته‌شده با rubpy انجام می‌شود.

```bash
python session_rubika.py
```

شماره موبایل و کد OTP را وارد کن. فایل `storage/playdl_rubika.rp` ساخته می‌شود. اگر این فایل نباشد دکمه روبیکا فعال است ولی هنگام آپلود پیام «Rubika غیرفعال است» می‌گیری.

روبیکا روی اکانت کاربری اجازه آپلود `.apk` نمی‌دهد، پس ربات قبل از ارسال فایل را داخل `NitoNumber-1.zip` بسته‌بندی می‌کند. برای جلوگیری از timeout روی APKهای بزرگ، آپلودر sequential ۱ مگابایتی rubpy موقع startup با یک پچ جایگزین می‌شود که ۸ chunk را موازی بالا می‌فرستد — تابع `_parallel_upload_file` در `Services/rubika.py`. اگر DC روبیکا rate-limit کرد، مقدار `RUBIKA_UPLOAD_CONCURRENCY` همان فایل را پایین بیار.

تنظیمات `.env`:

```env
RUBIKA_SESSION_NAME=playdl_rubika
RUBIKA_SESSION_DIR=storage
RUBIKA_MAX_FILE_MB=500
RUBIKA_UPLOAD_TIMEOUT=900
```

## اجرا

```bash
python Main.py
```

## تبدیل Split APK چطور انجام می‌شود؟

اگر دانلودر خروجی زیر را بدهد:

- یک `.apk`: همان فایل ارسال می‌شود
- یک `.apks`: با APKEditor به `.apk` تبدیل می‌شود
- چند split APK داخل یک پوشه: پوشه با APKEditor به `merged.apk` تبدیل می‌شود

اگر `alltech-gplay` با `MERGE_SPLITS=true` فعال باشد، اول خودش merge را انجام می‌دهد. اگر باز هم خروجی split بود، PlayDL مرحله merge با APKEditor را اجرا می‌کند.

## ساختار پروژه

```text
App/        شروع bot و تنظیمات
Handlers/   هندلرهای class-based aiogram
DataBase/   لایه MongoDB
Services/   دانلود، تبدیل و مدیریت job
Utils/      متن‌های فارسی و کیبوردهای inline
tools/      jarها و اسکریپت‌های اختیاری
storage/    فایل‌های دانلود و runtime
```
# مهم!
## این ربات بر روی Telegram-bot-api کار میکنه و باید خودتون روی سرورتون ستاپش کنید قبل از ران کردن این ربات


## دانلود چندمعماری

با `PLAY_ARCH_MODE=all` و `gplaydl 4.x` چهار ABI یعنی ARM64 (arm64-v8a)، ARMv7 (armeabi-v7a)، x86_64 و x86 درخواست می‌شوند. هر معماری جداگانه دانلود و تبدیل می‌شود و همراه `ARCHITECTURE_REPORT.json` داخل ZIP قرار می‌گیرد. خطای هر معماری برای همان برنامه در manifest ثبت می‌شود.

Google Play برای برنامه‌های App Bundle یک APK یونیورسال ارائه نمی‌کند. خروجی ربات چهار APK مجزای معماری در ZIP است، نه یک APK یونیورسال؛ فایل‌های mergeشده نیز دوباره امضا می‌شوند و روی نصب Play-signed قبلی قابل update نیستند.

گزینه «هر دو» همان ZIP را در تلگرام ارسال و در NixFile آپلود می‌کند و لینک آن را برمی‌گرداند.
