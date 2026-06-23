# Rebelway - Python For Production: Week 07 Report

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 14 file (bao gồm các bài học lý thuyết về nguyên lý SOLID, quy trình Agile/Scrum, các thư viện phân tích dữ liệu NumPy, Pandas, Matplotlib, Seaborn, Plotly và ứng dụng trực quan hóa 3D trực tiếp trong viewport Houdini).
- **Chủ đề chính của tuần:**
  - **Nguyên lý thiết kế SOLID (SOLID Principles):** Tìm hiểu sâu về 5 nguyên lý thiết kế hướng đối tượng (SRP, OCP, LSP, ISP, DIP) dưới góc nhìn của một Technical Artist. Cách tiếp cận viết code trong sản xuất: ưu tiên tính năng hoạt động trước (Functionality first), sau đó tiến hành tái cấu trúc (Refactoring). Phân tích ví dụ thực tế về việc refactor một công cụ GUI Unreal Engine vi phạm SRP để chia nhỏ thành các lớp helper chuyên biệt.
  - **Quy trình quản lý dự án Agile/Scrum:** Phân biệt triết lý Agile với mô hình Waterfall truyền thống dễ gây thời gian chết (downtime). Tìm hiểu cấu trúc vận hành Scrum bao gồm các vai trò (Product Owner, Scrum Master, Crew), các tài liệu (Product Backlog, User Stories, Sprint Backlog, Burndown Chart) và các nghi thức nghi lễ (Sprint Planning, Daily Scrum, Sprint Review/Retrospective).
  - **Nền tảng Khoa học Dữ liệu (Data Science Basics):** Làm quen với môi trường lập trình tương tác cell-based (Jupyter Notebook / IPython kernel) và cấu trúc mảng đa chiều NumPy (`arange`, `zeros`, `ones`, `linspace`, `eye`, `reshape`, `astype`).
  - **Phân tích và Dọn dẹp Dữ liệu bằng Pandas:** Sử dụng Pandas (`pd.read_csv`, DataFrame, Series, `head`, `info`, `describe`, `.loc` vs `.iloc`, filtering, `crosstab`, `groupby`, `.str.replace()`, `.isnull().sum()`, `.dropna()`, `pd.date_range()`, `df.T`, `sort_values()`, `df.drop()`) để dọn dẹp, biến đổi và quản lý các bảng dữ liệu lớn.
  - **Trực quan hóa dữ liệu (Data Visualization):** Sử dụng các thư viện vẽ biểu đồ từ cơ bản đến nâng cao:
    - **Matplotlib:** Vẽ biểu đồ scatter, subplots grid, histogram, boxplot để phân tích phân phối dữ liệu, và dựng đồ thị 3D bề mặt (`ax.plot_surface`) kết hợp đường đồng mức chiếu (`ax.contour`).
    - **Seaborn:** Vẽ biểu đồ thống kê chất lượng cao (`histplot`, `kdeplot`, `displot`, `relplot`, `jointplot`, `pairplot`). Phân tích bài toán mất cân bằng dữ liệu (data imbalance) để tránh ngụy biện thống kê.
    - **Plotly & Cufflinks:** Tạo biểu đồ tương tác 2D và 3D (`iplot`, bubble plot, scatter matrix, `go.Surface` với dữ liệu độ cao Mount Bruno) cho phép xoay, phóng to camera ngay trên trình duyệt web.
  - **Trực quan hóa dữ liệu trong Houdini (Plotting in Houdini viewport):** Tải dữ liệu từ Pandas/Seaborn ngay trong node Python SOP của Houdini, tự động sinh Point 3D bằng API `geo.createPoint()`, và dựng biểu đồ mật độ 3D động trong viewport bằng cách extrude mesh dựa trên thuộc tính mật độ tính bằng Wrangle.
- **Mục tiêu học tập chính:**
  - Nắm vững các nguyên lý SOLID để nâng cao tư duy thiết kế phần mềm, viết mã nguồn pipeline dễ bảo trì, dễ kiểm thử và mở rộng.
  - Hiểu cách thức vận hành dự án theo quy trình Agile/Scrum để phối hợp hiệu quả trong môi trường sản xuất studio chuyên nghiệp.
  - Làm chủ các thư viện khoa học dữ liệu cốt lõi (NumPy, Pandas) để xử lý dữ liệu lớn như file logs render, metadata assets, hay dữ liệu định vị địa lý.
  - Nắm vững các phương pháp trực quan hóa dữ liệu khác nhau (Matplotlib, Seaborn, Plotly) để phân tích dữ liệu hiệu suất và trình bày báo cáo trực quan.
  - Có khả năng xây dựng các công cụ phân tích dữ liệu không gian 3D tùy chỉnh ngay bên trong viewport của Houdini.

---

## 2. File-by-File Analysis

### 📄 File: 00_intro (1).txt

**Chủ đề chính:**
- Giới thiệu tổng quan nội dung tuần học 07.
- Sự chuyển dịch vai trò từ viết code công cụ pipeline sang khoa học dữ liệu (Data Science) cho Technical Artist.
- Giới thiệu các thư viện phân tích và trực quan hóa dữ liệu sẽ học trong tuần.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu lộ trình học tập của tuần 7. Giảng viên định hướng sự thay đổi trong tư duy của Technical Artist: từ việc chỉ viết các công cụ tự động hóa thủ công đơn lẻ sang việc khai thác dữ liệu sản xuất trên diện rộng. Tuần này sẽ trang bị cho học viên các nguyên lý viết code sạch (SOLID), quy trình quản lý dự án (Agile/Scrum), tiếp theo là các công cụ phân tích dữ liệu mạnh mẽ của Python như NumPy, Pandas, Matplotlib, Seaborn, Plotly và cách tích hợp trực quan hóa 3D trực tiếp trong viewport của Houdini.
- **Các khái niệm quan trọng:** Data Science, SOLID, Agile/Scrum, Data Visualisation (Matplotlib/Seaborn/Plotly), Houdini 3D viewport plotting.
- **Dạng nội dung:** Tổng quan định hướng (Overview).

**Mức độ sâu:**
- 🟢 Nông / Chủ yếu khái niệm.

**Điểm nổi bật:**
- Định hình rõ nét tầm quan trọng của dữ liệu trong sản xuất phim/game quy mô lớn và vai trò dẫn dắt của TA trong việc khai thác dữ liệu hiệu suất.

**Điểm hạn chế / Thiếu sót:**
- Không có phần viết mã hay minh họa thực tế do là video mở đầu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Định hướng tư duy về khoa học dữ liệu cho TA trong pipeline hiện đại.

---

### 📄 File: 01_solid_principles-001.txt

**Chủ đề chính:**
- 5 nguyên lý thiết kế hướng đối tượng SOLID (SRP, OCP, LSP, ISP, DIP).
- Triết lý viết code trong sản xuất: Tính năng chạy được trước (Functionality first), sau đó tiến hành tái cấu trúc (Refactoring).
- Phân tích lỗi thiết kế trong công cụ đặt tên thư mục Unreal Engine (Unreal Engine name assignment tool) từ các tuần trước.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên phân tích chi tiết 5 nguyên lý thiết kế SOLID. Nguyên lý đầu tiên và cốt lõi là Single Responsibility Principle (SRP) - một class chỉ nên có duy nhất một lý do để thay đổi. Giảng viên chỉ ra lỗi thiết kế trong công cụ đặt tên thư mục Unreal Engine (đã làm ở các tuần trước) khi một lớp GUI duy nhất vừa đảm nhận vẽ giao diện, vừa xử lý giải nén zip, xóa file và xuất CSV. Điều này vi phạm SRP nghiêm trọng vì khi định dạng zip hay CSV thay đổi, lớp GUI phải thay đổi theo. Cách khắc phục là tách logic giải nén và ghi CSV thành các lớp helper riêng biệt (`UnzipHelper`, `CSVExporter`). Ngoài ra, Open-Closed Principle (OCP) cũng được thảo luận sâu qua ví dụ về một hệ thống thanh toán cần được thiết kế mở rộng bằng tính kế thừa/interface thay vì sửa đổi class gốc bằng hàng loạt câu lệnh `if/else`.
- **Các khái niệm quan trọng:** SOLID principles, SRP, OCP, LSP, ISP, DIP, Code Refactoring, UI/Logic decoupling.
- **Dạng nội dung:** Lý thuyết thiết kế phần mềm & Phân tích thực tế (Software Design & Architecture).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Liên hệ trực tiếp đến kiến trúc code của các tool đã viết trong khóa học).

**Điểm nổi bật:**
- Đưa ra lời khuyên thực tế: Không nên quá lo lắng về SOLID ở giai đoạn đầu viết code vì sẽ làm nghẽn tư duy logic; hãy làm cho code chạy được trước (Functionality first) rồi mới refactor sau.

**Điểm hạn chế / Thiếu sót:**
- Chỉ giải thích lý thuyết bằng lời nói và sơ đồ phác thảo, thiếu phần viết code demo trực tiếp cấu trúc lớp trước và sau khi refactor.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ quan trọng để xây dựng các công cụ lớn, phức tạp trong studio mà không làm phát sinh lỗi dây chuyền (regression bugs) khi có thay đổi.

---

### 📄 File: 02_agile_scrum.txt

**Chủ đề chính:**
- Triết lý Agile vs Phương pháp truyền thống Waterfall.
- Các vai trò chính trong Scrum (Product Owner, Scrum Master, Crew/Team).
- Các tài liệu/Artifacts trong Scrum (Product Backlog, User Stories, Sprint Backlog, Burndown Chart).
- Các nghi thức/Ceremonies (Sprint Planning, Daily Scrum, Sprint Review/Retrospective).

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên giới thiệu về quy trình quản lý dự án hiện đại trong các studio game/VFX. waterfall là mô hình tuyến tính cũ, nơi các bộ phận phải đợi nhau làm xong mới bắt đầu (downtime cao). Agile khắc phục điều này bằng cách chia nhỏ sản phẩm thành các tính năng siêu nhỏ (micro-features) chạy đồng thời qua các Sprint dài 2-3 tuần. Trong Scrum, Product Owner chịu trách nhiệm định nghĩa tính năng ưu tiên (Product Backlog); Scrum Master đóng vai trò bảo vệ team, điều phối cuộc họp và giải quyết vướng mắc (blockers); còn Crew là nhóm phát triển trực tiếp. Học viên được học cách viết User Story chuẩn ("As a... I want to... so that...") và cách theo dõi tiến độ công việc bằng Burndown Chart hoặc Daily Stand-up.
- **Các khái niệm quan trọng:** Waterfall vs Agile, Scrum roles, Sprint cycles, User Stories, Backlogs, Burndown chart, Ceremonies.
- **Dạng nội dung:** Quy trình sản xuất & Quản lý dự án (Project Management & Studio pipeline).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rõ ràng các thuật ngữ và quy trình vận hành Scrum trong doanh nghiệp).

**Điểm nổi bật:**
- Giúp TA hiểu được cách giao dịch công việc, viết ticket chuẩn và báo cáo tiến độ hiệu quả trong các studio lớn sử dụng Agile.

**Điểm hạn chế / Thiếu sót:**
- Chỉ mô tả lý thuyết quy trình, chưa đi sâu vào việc hướng dẫn sử dụng các công cụ thực tế như Jira hay cách ước lượng Story Points cho các task đồ họa phức tạp.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – TA thường xuyên làm việc ở giao điểm của nghệ thuật và kỹ thuật nên việc hiểu Scrum giúp quản lý backlog công cụ cực kỳ tốt.

---

### 📄 File: 03_numpy_basics.txt

**Chủ đề chính:**
- Lập trình dựa trên các cell trong Jupyter Notebook (IPython kernel).
- Khái niệm mảng đa chiều NumPy (ndarray).
- Các phương thức khởi tạo mảng: `arange`, `zeros`, `ones`, `linspace`, `eye`.
- Thay đổi hình dạng mảng (`reshape`) và ép kiểu dữ liệu (`astype`).

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên giới thiệu môi trường lập trình tương tác Jupyter Notebook với IPython kernel, phân tích ưu nhược điểm của việc lưu trữ biến trong RAM khi chạy từng cell. Tiếp theo là các thao tác cơ bản trên NumPy: khởi tạo mảng số nguyên tuần tự bằng `np.arange()`, mảng chứa toàn số 0 hoặc số 1 bằng `np.zeros()` và `np.ones()`, mảng phân bố tuyến tính bằng `np.linspace()`, và ma trận đơn vị bằng `np.eye()`. Giảng viên demo cách thay đổi chiều mảng bằng `reshape()` và ép kiểu dữ liệu bằng `astype()`.
- **Các khái niệm quan trọng:** IPython kernel, ndarray, array creation, reshaping, type casting (`astype`).
- **Dạng nội dung:** Thực hành lập trình NumPy cơ bản (Python programming).

**Mức độ sâu:**
- 🟡 Trung bình (Các thao tác cơ bản nhưng cần thiết để làm quen với xử lý mảng).

**Điểm nổi bật:**
- So sánh rõ sự khác biệt giữa lập trình script truyền thống và lập trình tương tác cell-based (IPython), định hướng việc dùng NumPy làm backend hiệu năng cao cho các công cụ.

**Điểm hạn chế / Thiếu sót:**
- Chỉ demo toán học thuần túy trên các mảng số đơn giản, chưa có ứng dụng cụ thể vào đồ họa hay hình học ở bài này.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Là bước đệm để xử lý dữ liệu point/vertex nặng trong Houdini sau này.

---

### 📄 File: 04_python_csv_api.txt

**Chủ đề chính:**
- Đọc file CSV bằng thư viện chuẩn `csv` (`csv.reader` và `csv.DictReader`).
- Xử lý mã hóa font chữ (encoding như `utf-8`) khi đọc file chứa ký tự đặc biệt.
- Viết dữ liệu ra file CSV bằng `csv.writer` và `csv.DictWriter` (`writeheader`, `writerow`).
- Ứng dụng: Viết node Python SOP tùy chỉnh trong Houdini để đọc dữ liệu tọa độ từ file CSV và sinh Point tự động.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên hướng dẫn sử dụng thư viện `csv` của Python để đọc/ghi tệp dữ liệu phẳng. Sử dụng `csv.DictReader` giúp trả về dữ liệu dạng dictionary (key-value) theo tên cột rất trực quan. Bài học lưu ý các lỗi encoding ký tự đặc biệt và cách giải quyết bằng tham số `encoding='utf-8'`. Giảng viên thực hiện ghi tọa độ các điểm thành phố ra file `points.csv`. Sau đó, trong Houdini, giảng viên viết mã trong node Python SOP để đọc tệp CSV này, dùng hàm `next(reader, None)` để bỏ qua dòng tiêu đề, giải nén từng dòng thành float `(x, y, z)` và dùng API Houdini `geo.createPoint()` kết hợp `point.setPosition()` để dựng point 3D thực tế trong không gian 3D.
- **Các khái niệm quan trọng:** csv.DictReader, csv.writer, encoding='utf-8', header skipping, `geo.createPoint()`, `setPosition()` in Houdini Python.
- **Dạng nội dung:** Thực hành lập trình pipeline & tích hợp DCC (Houdini integration).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Tích hợp trực tiếp việc đọc tệp ngoài để tạo hình học trong Houdini).

**Điểm nổi bật:**
- Giúp học viên thấy ngay giá trị thực tế của việc xử lý dữ liệu ngoài: chỉ với vài dòng Python, TA có thể biến dữ liệu địa lý hoặc bảng tính CSV thành mesh/points trong Houdini.

**Điểm hạn chế / Thiếu sót:**
- Thư viện `csv` chuẩn của Python khá thô sơ khi cần thực hiện các thao tác lọc hay biến đổi dữ liệu phức tạp.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ hữu dụng để nhập dữ liệu camera, điểm định vị (locators), hoặc dữ liệu đo đạc bên ngoài vào cảnh Houdini.

---

### 📄 File: 05_intro_to_pandas01.txt

**Chủ đề chính:**
- Giới thiệu thư viện Pandas: DataFrame và Series.
- Đọc dữ liệu CSV bằng `pd.read_csv()`.
- Khảo sát nhanh dữ liệu bằng `head()`, `info()`, `describe()`.
- Truy xuất dữ liệu bằng Indexing: `.loc` (label-based) và `.iloc` (integer-based).
- Lọc dữ liệu theo điều kiện và thực hiện các phép gom nhóm đơn giản (`groupby`, `crosstab`).

**Nội dung chi tiết:**
- **Tóm tắt:** Pandas là thư viện hàng đầu cho phân tích dữ liệu dạng bảng. DataFrame biểu diễn bảng 2D, còn Series biểu diễn mảng 1D (cột). Giảng viên hướng dẫn đọc dữ liệu CSV vào DataFrame và dùng `info()` để xem kiểu dữ liệu, `describe()` để xem thống kê mô tả (mean, std, min, max, quartiles). Phân biệt kỹ lưỡng `.loc` (truy cập theo nhãn dòng/cột) và `.iloc` (truy cập theo vị trí số nguyên từ 0). Cuối cùng, thực hiện lọc các hàng thỏa mãn điều kiện và dùng `.groupby()` để gom nhóm dữ liệu (ví dụ tính trung bình chiều dài vây cánh chim cánh cụt theo từng loài).
- **Các khái niệm quan trọng:** pd.read_csv, DataFrame vs Series, `.info()`, `.describe()`, `.loc` vs `.iloc`, filtering, groupby, crosstab.
- **Dạng nội dung:** Phân tích dữ liệu thực hành (Data Analysis).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích cặn kẽ các hàm nền tảng nhất của Pandas).

**Điểm nổi bật:**
- Sự so sánh chi tiết và dễ hiểu giữa `.loc` (có thể trả về nhiều hàng nếu nhãn bị trùng) và `.iloc` (luôn trả về duy nhất một phần tử theo index tuyệt đối).

**Điểm hạn chế / Thiếu sót:**
- Mới chỉ ở mức làm quen trên tập dữ liệu mẫu chuẩn (penguins, tips), chưa tự tạo dữ liệu phức tạp.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Giúp TA phân tích các báo cáo render (render logs), dữ liệu asset trong pipeline một cách có hệ thống.

---

### 📄 File: 06_intro_to_pandas02.txt

**Chủ đề chính:**
- Ép kiểu dữ liệu trong cột Pandas (`astype()`) kết hợp các kiểu dữ liệu của NumPy.
- Làm sạch dữ liệu chuỗi (String cleaning) bằng `.str.replace()`.
- Lọc dữ liệu đa điều kiện bằng các toán tử logic bitwise `&` (AND) và `|` (OR).
- Kiểm tra và xử lý dữ liệu rỗng (`.isnull().sum()`, `.dropna()`).
- Vẽ biểu đồ tích hợp sẵn của Pandas (`df.plot()`, `df.hist()`).

**Nội dung chi tiết:**
- **Tóm tắt:** Hướng dẫn các kỹ thuật tiền xử lý dữ liệu (data preprocessing). Đầu tiên, ép kiểu dữ liệu từ float sang integer bằng `astype('int16')` hoặc các kiểu NumPy cụ thể để tối ưu bộ nhớ. Thứ hai, làm sạch dữ liệu văn bản bằng các hàm chuỗi của Pandas như xóa ký tự hashtag `#` khỏi cột hashtags bằng `.str.replace('#', '')`. Thứ ba, lọc dữ liệu phức tạp kết hợp nhiều điều kiện (ví dụ: lấy các bài viết có likes > 100 VÀ retweets < 10), nhấn mạnh việc bao bọc các điều kiện trong dấu ngoặc đơn. Thứ tư, xử lý các giá trị NaN/Null bằng cách đếm `.isnull().sum()` và loại bỏ dòng lỗi bằng `.dropna()`. Cuối cùng, demo khả năng vẽ biểu đồ nhanh trực tiếp từ Pandas bằng cách gọi các hàm vẽ tích hợp.
- **Các khái niệm quan trọng:** astype(), .str.replace(), boolean filtering (`&`/`|`), isnull(), dropna(), df.plot().
- **Dạng nội dung:** Tiền xử lý dữ liệu và vẽ đồ thị cơ bản (Data Preprocessing & Visualization).

**Mức độ sâu:**
- 🟡 Trung bình (Các thao tác biến đổi dữ liệu thực tế).

**Điểm nổi bật:**
- Nhấn mạnh việc ép kiểu dữ liệu tối ưu (ví dụ dùng `int16` thay vì `int64` mặc định) để tiết kiệm bộ nhớ RAM khi xử lý các bảng dữ liệu khổng lồ trong studio.

**Điểm hạn chế / Thiếu sót:**
- Phần xử lý dữ liệu null mới dừng lại ở mức bỏ qua dòng (`dropna`), chưa đi sâu vào việc điền giá trị trung bình/nội suy (imputation) cho các cột số.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ thiết thực để dọn dẹp các tệp metadata, quản lý file log render hoặc dữ liệu tracking dự án trước khi đưa vào hệ thống phân tích.

---

### 📄 File: 07_advanced_pandas_workflows.txt

**Chủ đề chính:**
- Tạo chuỗi thời gian tự động bằng `pd.date_range()`.
- Phân tích và truy xuất thuộc tính ngày tháng (DateTime properties như `.day`, `.month`, `.year`).
- Chuyển vị dữ liệu (Transpose DataFrame bằng `df.T`).
- Sắp xếp dữ liệu theo cột bằng `sort_values()`.
- Sử dụng mảng NumPy làm dữ liệu đầu vào cho DataFrame và thiết lập Custom Index.
- Loại bỏ các cột dữ liệu không cần thiết bằng `drop()`.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên trình bày các workflow nâng cao với Pandas. Bắt đầu bằng cách tạo một cột chứa dữ liệu thời gian tự động qua `pd.date_range(start, periods, freq)` và minh họa cách truy cập trực tiếp các thuộc tính thời gian như `.day`. Tiếp theo, giảng viên hướng dẫn cách chuyển vị dòng và cột của DataFrame bằng `df.T` và cách sắp xếp dữ liệu tăng/giảm dần bằng `sort_values(by=..., ascending=...)`. Cuối cùng, hướng dẫn khởi tạo DataFrame từ ma trận NumPy ngẫu nhiên, gán index bằng danh sách tên custom và cách xóa bớt cột bằng lệnh `df.drop(columns=[...])`.
- **Các khái niệm quan trọng:** pd.date_range, DateTime index, Transpose (`df.T`), `sort_values()`, df.drop().
- **Dạng nội dung:** Thao tác dữ liệu nâng cao (Advanced DataFrame manipulation).

**Mức độ sâu:**
- 🟡 Trung bình (Cung cấp các kỹ năng biến đổi cấu trúc bảng linh hoạt).

**Điểm nổi bật:**
- Việc sử dụng DateTime làm Index cho DataFrame mở ra khả năng phân tích dữ liệu chuỗi thời gian (time-series analysis), rất phù hợp để theo dõi hiệu suất hệ thống theo thời gian thực.

**Điểm hạn chế / Thiếu sót:**
- Thiếu phần ví dụ về việc gộp (Merge/Join) nhiều DataFrame khác nhau, vốn là một phần rất quan trọng khi làm việc với nhiều nguồn dữ liệu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Giúp xoay trục (transpose) bảng dữ liệu thuộc tính mesh hoặc sắp xếp các asset theo dung lượng để tìm ra file nặng nhất.

---

### 📄 File: 08_intro_to_matplotlib.txt

**Chủ đề chính:**
- Sử dụng module `matplotlib.pyplot` như thư viện trực quan hóa dữ liệu chuẩn.
- Tạo dữ liệu mô phỏng hình tròn/cụm điểm bằng `datasets.make_circles` và `datasets.make_blobs` của `scikit-learn`.
- Cấu hình kích thước hình ảnh (`figsize`) và vẽ biểu đồ scatter.
- Chia nhỏ vùng vẽ thành lưới subplot (`plt.subplots()`).
- Vẽ biểu đồ phân bố tần suất (Histogram) và biểu đồ hộp (Boxplot).

**Nội dung chi tiết:**
- **Tóm tắt:** Bắt đầu phần trực quan hóa dữ liệu chuyên sâu với Matplotlib. Để có dữ liệu trực quan thú vị, giảng viên cài đặt thư viện `scikit-learn` và dùng hàm sinh dữ liệu hình học như `make_circles()` và `make_blobs()`. Tiếp theo, giảng viên vẽ biểu đồ scatter với màu sắc điểm thay đổi theo nhãn phân lớp bằng đối số `c=Y` và colormap `cmap`. Bài học hướng dẫn cách khởi tạo một canvas có nhiều vùng vẽ bằng `fig, ax = plt.subplots(rows, cols)`, cách cấu hình trục, lưới và vẽ các dạng biểu đồ phân tích thống kê cốt lõi như Histogram (phân phối tần suất) và Boxplot (phân phối tứ phân vị, phát hiện ngoại lai).
- **Các khái niệm quan trọng:** make_circles, make_blobs, plt.subplots(), axes grid, plt.hist(), plt.boxplot().
- **Dạng nội dung:** Trực quan hóa dữ liệu cơ bản (Data Visualization).

**Mức độ sâu:**
- 🟡 Trung bình (Hướng dẫn đầy đủ các thao tác dựng biểu đồ 2D cơ bản).

**Điểm nổi bật:**
- Giới thiệu Boxplot - một công cụ thống kê cực mạnh để phát hiện các giá trị ngoại lai (outliers), ví dụ tìm các file có thời gian render bất thường.

**Điểm hạn chế / Thiếu sót:**
- Matplotlib yêu cầu viết nhiều dòng code cấu hình trục (labels, grid, legends) khá rườm rà so với các thư viện trực quan hóa bậc cao.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cần thiết để lập biểu đồ thống kê lỗi (render errors) hoặc biểu đồ phân tích hiệu suất cảnh.

---

### 📄 File: 09_advanced_matplotlib-009.txt

**Chủ đề chính:**
- Tùy chỉnh chi tiết đường cong vẽ (color, marker, linewidth) trên trục tọa độ.
- Sử dụng `ScalarFormatter` để hiển thị định dạng số khoa học ($10^x$) trên các trục tọa độ lớn.
- Dựng lưới bề mặt 3D tương tác tĩnh bằng `np.meshgrid` và `ax.plot_surface`.
- Cấu hình khoảng bước nhảy lưới (`rstride/cstride`) và tô màu theo Colormap (`viridis`, `coolwarm`).
- Chiếu các đường đồng mức (Contour plots) lên các mặt của trục tọa độ 3D.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học cung cấp các kỹ năng vẽ đồ thị kỹ thuật chuyên sâu bằng Matplotlib. Đầu tiên là việc căn chỉnh định dạng số lớn trên trục bằng `ticker.ScalarFormatter(useMathText=True)` giúp biểu diễn dữ liệu khoa học gọn gàng. Phần lớn thời lượng dành cho vẽ đồ thị 3D: import `Axes3D`, phân phối ma trận lưới XY bằng `np.meshgrid()`, tính độ cao Z và vẽ bề mặt bằng `ax.plot_surface()`. Giảng viên điều chỉnh độ mịn của lưới qua bước nhảy hàng/cột (`rstride`, `cstride`), thêm thanh chỉ dẫn màu sắc co giãn `fig.colorbar(shrink=0.5)` và chiếu các đường đồng mức lên mặt phẳng 3D bằng `ax.contour(X, Y, Z, zdir='z', offset=..., cmap=...)`.
- **Các khái niệm quan trọng:** ScalarFormatter, Axes3D, np.meshgrid, plot_surface, colormaps, rstride/cstride, contour projection.
- **Dạng nội dung:** Trực quan hóa dữ liệu nâng cao (Advanced 3D Visualization).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Can thiệp sâu vào cấu trúc ma trận lưới và chiếu tọa độ 3D).

**Điểm nổi bật:**
- Hướng dẫn chi tiết cách dựng lưới bề mặt 3D giúp học viên hiểu rõ cách phân phối ma trận dữ liệu không gian, liên hệ trực tiếp với cách phân phối lưới tọa độ trong đồ họa máy tính.

**Điểm hạn chế / Thiếu sót:**
- Matplotlib 3D tạo ra các hình ảnh tĩnh, không thể tương tác xoay camera trực quan bằng chuột, gây khó khăn khi muốn quan sát dữ liệu không gian ở nhiều góc độ.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA mô phỏng trực quan các hàm toán học 3D, phân bố tiếng ồn (Noise functions như Perlin/Simplex), hoặc trường vector lực (Force fields) trước khi lập trình vào DCC.

---

### 📄 File: 10_intro_to_seaborn_1.txt

**Chủ đề chính:**
- Sử dụng thư viện Seaborn vẽ biểu đồ thống kê bậc cao.
- Nạp các dataset tích hợp mẫu: 'flights', 'penguins', 'tips'.
- Vẽ biểu đồ tần suất xếp chồng `histplot(..., multiple='stack')` và biểu đồ mật độ liên tục `kdeplot()`.
- Phân tích tương quan dữ liệu chéo bằng `relplot()`, `jointplot()`, và ma trận tương quan toàn diện `pairplot()`.
- Bài toán mất cân bằng dữ liệu (data imbalance) và những sai lầm khi diễn giải đồ thị.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên hướng dẫn cách sử dụng Seaborn để vẽ biểu đồ thống kê nhanh chóng và đẹp mắt hơn Matplotlib. Trọng tâm của bài học là cách sử dụng thuộc tính `hue` để phân nhóm màu dữ liệu. Đặc biệt, giảng viên đưa ra ví dụ thực tế về dữ liệu tiền boa của nhà hàng: nếu chỉ nhìn vào đồ thị tip theo giới tính, ta thấy nam giới boa nhiều hơn. Nhưng khi vẽ đồ thị đếm mẫu (`histplot`), ta phát hiện mẫu nam giới chiếm số lượng áp đảo mẫu nữ giới trong tập dữ liệu. Đây là lỗi mất cân bằng dữ liệu (data imbalance) rất dễ dẫn đến kết luận ngụy biện nếu không khảo sát kỹ. Bài học kết thúc với các hàm trực quan tương quan như `relplot`, `jointplot` và `pairplot`.
- **Các khái niệm quan trọng:** sns.load_dataset, kdeplot, displot, ax mapping, relplot, jointplot, pairplot, data imbalance warning.
- **Dạng nội dung:** Trực quan hóa dữ liệu thống kê thực hành (Statistical Data Visualization).

**Mức độ sâu:**
- 🟡 Trung bình (Hướng dẫn cách dùng và diễn giải ý nghĩa thực tế của các đồ thị thống kê).

**Điểm nổi bật:**
- Bài học cảnh báo lỗi ngụy biện dữ liệu (misconception) cực kỳ sâu sắc khi phân tích biểu đồ mà không kiểm tra độ cân bằng của tập mẫu.

**Điểm hạn chế / Thiếu sót:**
- `pairplot()` đối với các tập dữ liệu có số lượng cột lớn sẽ chạy rất chậm và ngốn nhiều tài nguyên hệ thống do phải sinh ra ma trận biểu đồ cực lớn.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Rất hữu ích để TA phân tích thống kê dữ liệu sản xuất thực tế trong studio, như tương quan giữa số lượng light sources, polygon count và thời gian render.

---

### 📄 File: 11_plotting_in_houdini.txt

**Chủ đề chính:**
- Thiết lập thư viện phân tích dữ liệu (Seaborn, Pandas, Numpy) trong môi trường Python của Houdini.
- Sử dụng node Python SOP để nạp dataset 'penguins' và sinh điểm 3D tương ứng.
- Viết mã Wrangle để đo mật độ điểm lân cận và gán màu sắc `Cd`.
- Nhân bản lưới (grids) lên points và đẩy cao extrusion trục Y theo mức độ mật độ.
- Tạo đồ thị mật độ 3D trực quan ngay trong viewport của Houdini.

**Nội dung chi tiết:**
- **Tóm tắt:** Hướng dẫn kết hợp khoa học dữ liệu trực tiếp vào viewport 3D của Houdini. Giảng viên viết mã trong node Python SOP để import Seaborn, nạp dataset 'penguins', lặp qua từng hàng bằng `.iloc` và trích xuất hai cột vây cánh (`flipper_length_mm`) làm tọa độ X, chiều dài mỏ (`bill_length_mm`) làm tọa độ Z (Y gán bằng 0). Sau đó dùng `geo.createPoint()` dựng điểm. Tiếp theo, một node Attribute Wrangle tính toán mật độ phân bố điểm và gán vào màu `Cd` (càng đông đúc càng sáng). Cuối cùng, nhân bản lưới lên các điểm này và sử dụng vòng lặp extrude các lưới theo chiều cao trục Y dựa trên màu sắc. Kết quả tạo ra một mesh 3D dạng biểu đồ cột thể hiện mật độ dữ liệu trực quan trong không gian Houdini, khớp hoàn hảo với đồ thị 2D ngoài trình duyệt.
- **Các khái niệm quan trọng:** Python SOP dataset loading, point generation, xz-plane mapping, proximity color wrangle, loop-based primitive extrusion, 3D density chart.
- **Dạng nội dung:** Lập trình công cụ DCC nâng cao (Custom Houdini tool building).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Kết hợp nhuần nhuyễn giữa xử lý dữ liệu Pandas và các API hình học của Houdini).

**Điểm nổi bật:**
- Cho phép Technical Artist tự dựng các hệ thống trực quan hóa dữ liệu không gian 3D (như heatmap phân bố polygon, mật độ hạt, hiệu năng render cảnh) trực tiếp trong viewport để hỗ trợ nghệ sĩ làm việc.

**Điểm hạn chế / Thiếu sót:**
- Việc vẽ văn bản nhãn trục tọa độ trong viewport vẫn phải sử dụng node Font thủ công, chưa tự động hóa hoàn toàn theo metadata của DataFrame.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là ứng dụng thực tế đỉnh cao của việc đưa Data Science vào hỗ trợ sản xuất đồ họa 3D.

---

### 📄 File: 12_interactive_plotting.txt

**Chủ đề chính:**
- Thiết lập môi trường vẽ đồ thị tương tác ngoại tuyến qua **Plotly** và **Cufflinks**.
- Sử dụng phương thức `.iplot()` trực tiếp trên DataFrame để tạo đồ thị tương tác HTML.
- Sử dụng Bubble Plot và Scatter Matrix để khảo sát tương quan nhiều chiều của dữ liệu.
- Làm sạch dữ liệu trống (`.fillna()`) để tránh lỗi render của thư viện Javascript.
- Vẽ đồ thị bề mặt 3D tương tác (`go.Surface` với dữ liệu Mount Bruno) hỗ trợ xoay, thu phóng camera 3D trực tiếp trên trình duyệt.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu phương pháp trực quan hóa dữ liệu động bằng Plotly và Cufflinks. Người dùng có thể hover chuột để xem chi tiết thông số điểm, zoom/pan vào khu vực cụ thể và bật/tắt các lớp dữ liệu trên chú thích (legend). Giảng viên hướng dẫn vẽ đồ thị bong bóng (bubble plot) bằng cách map cột thứ ba vào kích thước bong bóng, vẽ ma trận phân tán tương tác, và tiền xử lý dữ liệu NaN bằng `.fillna(..., inplace=True)`. Cuối cùng, bài học thực hiện đọc file CSV chứa cao độ của đỉnh núi Mount Bruno và dựng bề mặt 3D tương tác bằng `go.Surface(z=cdata)`. Biểu đồ này cho phép người dùng xoay camera 3D tự do trực tiếp trên trình duyệt web.
- **Các khái niệm quan trọng:** Plotly Offline mode, Cufflinks integration (`df.iplot`), fillna() data cleaning, Bubble chart, Scatter matrix, go.Surface, 3D rotatable camera.
- **Dạng nội dung:** Lập trình trực quan hóa dữ liệu tương tác (Interactive Web Visualization).

**Mức độ sâu:**
- 🔴 Sâu / Kỹ thuật (Sử dụng các cấu hình layout phức tạp như margin, width, height, và định dạng dữ liệu bề mặt 3D).

**Điểm nổi bật:**
- Khả năng tương tác xoay camera 3D bằng chuột trên trình duyệt web giải quyết triệt để hạn chế của Matplotlib tĩnh, giúp việc khảo sát dữ liệu địa hình/không gian trở nên cực kỳ dễ dàng.

**Điểm hạn chế / Thiếu sót:**
- File HTML xuất ra từ Plotly thường có dung lượng lớn do đính kèm toàn bộ thư viện Javascript bên trong.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Rất hữu ích để TA xây dựng các dashboard báo cáo render động, hoặc trực quan hóa dữ liệu phân tích địa hình (heightmaps) tương tác cho studio.

---

### 📄 File: 14_assignment.txt

**Chủ đề chính:**
- Mô tả bài tập về nhà của tuần 07.
- Thu thập 2 dataset liên quan từ Kaggle.
- Sử dụng Pandas để trộn (Merge) hai dataset này thành một.
- Thực hiện vẽ ít nhất 5 loại đồ thị khác nhau trong Jupyter Notebook để phân tích dữ liệu mới.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên công bố bài tập về nhà tuần 07. Học viên phải lên Kaggle tìm và tải xuống hai tập dữ liệu khác nhau nhưng có mối liên quan nào đó (ví dụ: dữ liệu thời tiết và dữ liệu nông nghiệp, hoặc dữ liệu phim và doanh thu). Sau đó sử dụng Pandas để gộp hai bảng này lại thành một. Dựa trên dữ liệu gộp mới, học viên phải viết Jupyter Notebook dựng ít nhất 5 loại đồ thị khác nhau (như Histogram, KDE, Bar, Scatter, Joint) thể hiện mối tương quan hoặc phân bố của các cột.
- **Các khái niệm quan trọng:** Kaggle dataset sourcing, Pandas dataframe merge, 5 distinct plot types implementation, Jupyter Notebook submission.
- **Dạng nội dung:** Bài tập thực hành tổng hợp (Week Assignment).

**Mức độ sâu:**
- 🟡 Trung bình (Yêu cầu vận dụng tổng hợp các kỹ năng xử lý và trực quan hóa dữ liệu đã học).

**Điểm nổi bật:**
- Rèn luyện kỹ năng gộp dữ liệu (merge) - một tác vụ cực kỳ phổ biến trong thực tế khi dữ liệu sản xuất thường bị phân mảnh ở nhiều file/hệ thống khác nhau.

**Điểm hạn chế / Thiếu sót:**
- Đề bài mở, không giới hạn cụ thể tập dữ liệu nào nên học viên phải tự tìm kiếm và tự đánh giá tính hợp lý của mối quan hệ giữa các cột khi gộp.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA tự lập trong việc tìm kiếm, xử lý và trực quan hóa các dữ liệu phức tạp ngoài thực tế sản xuất.

---

## 3. Weekly Summary

### Tổng kết nội dung học tập
Week 07 cung cấp một cái nhìn toàn diện từ các nguyên lý viết code sạch trong sản xuất (SOLID), quy trình quản lý dự án (Agile/Scrum) đến các công cụ Khoa học dữ liệu (Data Science) mạnh mẽ nhất của Python (NumPy, Pandas, Matplotlib, Seaborn, Plotly). Đặc biệt là sự tích hợp tuyệt vời giữa xử lý dữ liệu và DCC Houdini để tạo ra các biểu đồ 3D viewport sống động.

### Bài học cốt lõi & Tư duy Technical Artist
1. **SOLID & decoupled architecture:** TA tools thường vi phạm Single Responsibility Principle do gom cả UI, logic xử lý file và logic xuất dữ liệu vào một class duy nhất. Việc tái cấu trúc (refactoring) tách biệt logic nghiệp vụ ra các lớp helper chuyên biệt giúp hệ thống dễ mở rộng, dễ viết unit tests và hạn chế tối đa việc gây lỗi dây chuyền.
2. **Triết lý sản xuất "Functionality first":** Không nên quá ám ảnh bởi code sạch ngay từ đầu dẫn đến tắc nghẽn thiết kế; hãy làm cho công cụ hoạt động được trước, sau đó mới dọn dẹp và tối ưu hóa code ở giai đoạn refactor.
3. **Hiểu quy trình Agile/Scrum:** Giúp TA chủ động quản lý backlog công cụ, viết tài liệu User Stories đúng chuẩn, theo dõi tiến độ qua Burndown Chart và phối hợp nhịp nhàng với đội ngũ nghệ sĩ và lập trình viên trong các buổi Daily Scrum.
4. **Khai thác dữ liệu lớn:** Tận dụng Pandas để dọn dẹp dữ liệu trống (`fillna`/`dropna`), đổi tên cột, ép kiểu dữ liệu tối ưu (`int16`/`int32`) để tiết kiệm RAM, và lọc dữ liệu đa điều kiện (`&`/`|`).
5. **Cảnh giác với mất cân bằng dữ liệu (Data Imbalance):** Khi diễn giải đồ thị thống kê, luôn phải kiểm tra số lượng mẫu (sample size) của các nhóm đối tượng để tránh đưa ra kết luận sai lệch (misconception).
6. **Viewport-in data visualizer:** Sự kết hợp giữa Pandas trong node Python SOP và Attribute Wrangle trong Houdini cho phép TA xây dựng các công cụ phân tích hình học hoặc hiệu suất cảnh 3D trực quan cực kỳ mạnh mẽ dưới dạng mesh/points 3D ngay trong không gian làm việc của nghệ sĩ.
7. **Trực quan hóa tương tác:** Plotly và Cufflinks mở ra khả năng xây dựng các dashboard báo cáo render hoặc phân tích địa hình 3D tương tác ( Mount Bruno elevation) có thể xoay camera bằng chuột trực tiếp trên trình duyệt web, giúp nâng cao chất lượng báo cáo cho cấp quản lý.
