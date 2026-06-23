# Rebelway - Python For Production: Week 03 Report

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 17 file.
- **Chủ đề chính của tuần:**
  - Khái niệm cơ bản về DevOps, CI/CD và ứng dụng tự động hóa trong pipeline sản xuất VFX & ML.
  - Sử dụng Git nâng cao: Forking, cấu hình upstream, đồng bộ hóa nhánh, và quản lý nhiều nhánh làm việc song song bằng Git Worktrees thông qua bare repository.
  - Tải/nạp dữ liệu từ đám mây (Google Drive API) và tổ chức dữ liệu cấu hình metadata bằng JSON.
  - Tư duy thiết kế hệ thống (System Design): Clients, Servers, Latency, Throughput, Caching, Load Balancers, và các loại hình lưu trữ (Blob storage, Key-value pairs).
  - Lập trình hướng đối tượng nâng cao: Encapsulation (Access modifiers: Public, Protected, Private) và các bộ trang trí `@property` (Getters, Setters, Deleters).
  - Đọc/ghi cấu hình tệp YAML (`PyYAML`), tự động sinh cấu hình Houdini Packages JSON để thay thế tệp `houdini.env` truyền thống.
  - Tự động hóa hệ thống bằng shell script (`.sh`).
  - Xây dựng cặp công cụ Publisher Node và Asset Loader Node hoàn chỉnh trong Houdini, tích hợp cơ chế nạp code ngoài (`sys.path.append`) và tự động sinh menu phiên bản động (Menu Script).
- **Mục tiêu học tập chính:**
  - Xây dựng tư duy phát triển hệ thống (System Design) và DevOps để quản lý các pipeline phân tán.
  - Làm chủ kỹ năng quản lý phiên bản với Git nâng cao và tự động hóa QC (Quality Control) trong CI/CD.
  - Triển khai thành công quy trình đóng gói và phân phối tool trong studio bằng Houdini Packages.
  - Phát triển thành thạo các HDA tương tác trực tiếp với cloud storage (Google Drive), tự động quản lý phiên bản (versioning) và nạp asset động theo giao diện Menu.

---

## 2. File-by-File Analysis

### 📄 File: 01_intro.txt

**Chủ đề chính:**
- Giới thiệu tổng quan nội dung Week 03.
- Khái niệm DevOps, CI/CD và kết nối API với Google Drive.
- Lý thuyết System Design áp dụng vào VFX pipeline.
- Quản lý file cấu hình YAML, tính đóng gói (encapsulation) trong Python.
- Houdini Packages và xây dựng Publisher Node.

**Nội dung chi tiết:**
- **Tóm tắt:** File này là transcript giới thiệu tổng quan của tuần 3. Giảng viên phác thảo lộ trình học tập, nhấn mạnh việc chuyển dịch từ lập trình script đơn lẻ sang tư duy phát triển hệ thống lớn (DevOps, CI/CD, System Design). Học viên sẽ học cách xây dựng pipeline kết nối đám mây (Google Drive), quản lý dữ liệu bằng tệp YAML/JSON, tự động hóa môi trường làm việc thông qua Houdini Packages và kết thúc bằng việc tự tay viết một Publisher Node để kiểm soát việc xuất bản tài nguyên.
- **Các khái niệm quan trọng:** CI/CD, System Design, YAML, Houdini Packages, Publisher Node.
- **Dạng nội dung:** Lý thuyết giới thiệu khái quát (Overview).

**Mức độ sâu:**
- 🟢 Nông / Chủ yếu khái niệm (Chỉ liệt kê danh mục kiến thức và lộ trình học tập của tuần).

**Điểm nổi bật:**
- Nhấn mạnh việc thiết kế một "publisher node" như một khung xương (bare skeleton) để TA tự phát triển và nâng cấp theo đặc thù công việc.

**Điểm hạn chế / Thiếu sót:**
- Không đi sâu vào chi tiết kỹ thuật vì đây là bài mở đầu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Định hướng lộ trình học tập để TA hiểu cách các công cụ riêng lẻ liên kết với nhau trong một hệ thống sản xuất.

---

### 📄 File: 02_ci_cd.txt

**Chủ đề chính:**
- Định nghĩa DevOps và CI/CD (Continuous Integration & Continuous Deployment).
- Vòng đời phần mềm dưới dạng vòng lặp vô hạn (Plan -> Code -> Build -> Test -> Release -> Deploy -> Operate -> Monitor).
- So sánh vòng đời phần mềm với Vòng đời dự án VFX (Project Life Cycle - Project Charter, KPI, Client Feedback).
- Khái niệm MLOps (Machine Learning Operations) trong quản lý mô hình AI.
- Tầm quan trọng của việc giám sát (Monitoring) và tự động hóa các khâu kiểm thử.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học cung cấp cái nhìn tổng quan về DevOps và CI/CD, giải thích cơ chế tự động hóa quy trình tích hợp và triển khai phần mềm. Giảng viên vẽ ra mối liên hệ trực quan giữa vòng đời phát triển phần mềm với thực tế quản lý shot trong VFX (nơi shot được lập kế hoạch, phân chia task cho junior/senior, sản xuất, gửi khách hàng duyệt, nhận ghi chú phản hồi và quay lại sửa đổi). Đồng thời, bài học giới thiệu sơ bộ về MLOps (quy trình thu thập dữ liệu, huấn luyện, đóng gói container và giám sát hiệu suất mô hình AI). Giảng viên nhấn mạnh rằng mọi phần mềm hay pipeline đều là thực thể sống cần liên tục nâng cấp và tự động hóa các bước kiểm thử (test cases) để tránh lỗi con người.
- **Các khái niệm quan trọng:** DevOps loop, Continuous Integration, Continuous Deployment, Project Management Lifecycle, MLOps, Automated feedback & monitoring.
- **Dạng nội dung:** Lý thuyết tư duy hệ thống và quy trình sản xuất (System & Project Management).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rất rõ về mặt triết lý vận hành của DevOps/VFX/ML và các bước trong một vòng lặp kín, nhưng chưa đi sâu vào các tool tự động hóa cụ thể).

**Điểm nổi bật:**
- Khéo léo so sánh vòng lặp DevOps trong ngành IT với quy trình làm shot/asset và nhận feedback từ đạo diễn trong ngành VFX, giúp nghệ sĩ dễ dàng đồng cảm và tiếp thu tư duy lập trình hệ thống.

**Điểm hạn chế / Thiếu sót:**
- Thiếu phần giới thiệu các công cụ CI/CD phổ biến (như GitHub Actions, Jenkins hoặc GitLab CI) thường dùng trong studio.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Hiểu DevOps giúp TA biết cách vận hành một hệ thống phân phối tool tự động cho toàn studio, thay vì gửi file code thủ công qua chat/email.

---

### 📄 File: 03_git_01.txt

**Chủ đề chính:**
- Phân biệt giữa công nghệ Git và các nền tảng đám mây (GitHub, GitLab).
- Quy trình dòng lệnh cơ bản: `clone`, `status`, `add`, `commit`, `push`.
- Phân nhánh dự án bằng `git checkout -b` để cách ly mã nguồn thử nghiệm.
- Khái niệm Pull Request (PR) và quy trình code review của supervisor/senior.
- Bảo mật kết nối bằng SSH keys (tiêu chuẩn công ty) thay vì HTTPS và Personal Access Token (PAT).
- Viết tệp `.gitignore` để tránh đẩy file nặng hoặc file cache lên đám mây.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học thực hành hướng dẫn các thao tác cơ bản và nâng cao với Git. Giảng viên giải thích sự khác biệt giữa Git (nhân phiên bản cốt lõi) và GitHub (giao diện API). Đi sâu vào quy trình làm việc nhóm chuyên nghiệp: các lập trình viên/TA không bao giờ được viết code trực tiếp trên nhánh `main`, thay vào đó phải tạo nhánh con bằng `git checkout -b`, thực hiện code, commit địa phương, và push lên repository của mình. Tiếp theo, lập trình viên tạo một Pull Request (PR) để supervisor đánh giá các commit khác biệt, chạy kiểm thử, trước khi đồng ý gộp (merge) code vào nhánh `main` chung. Giảng viên cũng lưu ý việc cấu hình SSH keys để bảo mật thay vì HTTPS, và cấu hình `.gitignore` để loại bỏ các tệp tin rác hoặc file hình học quá nặng.
- **Các khái niệm quan trọng:** Version Control, Git branch lifecycle, Pull Request (PR), Code Review, SSH vs HTTPS security, `.gitignore` syntax.
- **Dạng nội dung:** Thực hành dòng lệnh Git và giao diện GitHub.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn từng lệnh Git thực tế từ tạo nhánh, kiểm tra trạng thái, commit tin nhắn, đẩy mã nguồn, và thực hiện merge PR trên giao diện GitHub).

**Điểm nổi bật:**
- Nhấn mạnh triết lý phân nhánh (branching) như một cấu trúc cây dữ liệu, giúp TA cô lập hoàn toàn môi trường code thử nghiệm, tránh làm hỏng các công cụ đang chạy ổn định của studio.

**Điểm hạn chế / Thiếu sót:**
- Chưa hướng dẫn cách giải quyết xung đột mã nguồn (merge conflicts) khi hai lập trình viên cùng sửa đổi một dòng code.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Kỹ năng Git là bắt buộc khi TA làm việc trong các dự án lớn có sự tham gia của nhiều lập trình viên/artist, đảm bảo mã nguồn của tool luôn được quản lý phiên bản an toàn.

---

### 📄 File: 04_git_02.txt

**Chủ đề chính:**
- Quy trình đóng góp mã nguồn mở thông qua tính năng Forking trên GitHub.
- Khái niệm liên kết repository gốc (`upstream`) và repository bản sao (`origin`).
- Cách cấu hình remote upstream bằng lệnh `git remote add upstream`.
- Đồng bộ hóa cập nhật từ dự án gốc bằng lệnh `git fetch upstream` và `git merge`.
- Kỹ thuật giữ code địa phương không bị xung đột (out of sync) với các thay đổi của cộng đồng.

**Nội dung chi tiết:**
- **Tóm tắt:** File học hướng dẫn cách tham gia đóng góp cho các dự án nguồn mở (open-source) hoặc phối hợp giữa các studio đối tác. Khi fork một repository (ví dụ như thư viện `tinygrad`), học viên tạo một bản sao độc lập của repo đó về tài khoản cá nhân. Để giữ cho bản fork này luôn cập nhật các tính năng mới từ repo gốc của tác giả mà không làm mất các chỉnh sửa cá nhân, giảng viên hướng dẫn quy trình đồng bộ hóa: đăng ký địa chỉ repo gốc làm remote tên là `upstream`, chạy `git fetch upstream` để tải các thay đổi mới về máy, chuyển sang nhánh làm việc và chạy `git merge upstream/master` (hoặc tên nhánh gốc) để gộp code.
- **Các khái niệm quan trọng:** Forking, Origin vs Upstream remotes, `git remote add upstream`, `git fetch upstream`, Synching forks, Code alignment.
- **Dạng nội dung:** Thực hành quản lý remote repository và đồng bộ hóa nhánh.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Giải thích cấu trúc liên kết 3 lớp: Repo gốc -> Repo Fork trên đám mây -> Repo làm việc dưới máy địa phương, và các lệnh đồng bộ tương ứng).

**Điểm nổi bật:**
- Giải thích rõ ràng sự cần thiết phải đồng bộ hóa thường xuyên bằng lệnh `fetch upstream` trước khi viết code mới để tránh xung đột mã nguồn nghiêm trọng khi tạo PR.

**Điểm hạn chế / Thiếu sót:**
- Không đề cập đến các rủi ro khi đồng bộ nếu repo gốc thay đổi hoàn toàn kiến trúc API (breaking changes).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cần thiết khi TA tích hợp và chỉnh sửa các thư viện mã nguồn mở VFX (như OpenVDB, USD, PySide) hoặc khi phối hợp phát triển pipeline dùng chung giữa các studio con.

---

### 📄 File: 05_git_03.txt

**Chủ đề chính:**
- Giới thiệu khái niệm nâng cao **Git Worktrees** trong lập trình song song.
- Khắc phục nhược điểm của việc stash code hoặc clone nhiều thư mục repo.
- Kỹ thuật clone bare repository (`git clone --bear <url>`).
- Cách tạo và quản lý song song nhiều nhánh làm việc dưới dạng các thư mục vật lý độc lập.
- Quy trình kiểm thử (QC/Automated testing) trong CI/CD pipeline bằng Python.
- Viết test runner script kiểm tra thuật toán Binary Search với các trường hợp mẫu (test cases).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu **Git Worktrees** – giải pháp thay thế tối ưu cho việc chuyển đổi nhánh liên tục khi phải đổi task đột xuất để xử lý sự cố. Bằng cách sử dụng clone dạng bare (`git clone --bear`), các nhánh (ví dụ: `master`, `test1`, `test2`) được ánh xạ thành các thư mục vật lý riêng biệt trên ổ cứng. Lập trình viên có thể mở nhiều editor làm việc trên các nhánh này song song mà không cần stash code hay làm bẩn thư mục làm việc hiện tại. Ở phần hai, giảng viên giới thiệu cơ chế kiểm thử tự động (QC) trong CI/CD. Đoạn code Python SOP hoặc script pipeline trước khi được deploy sẽ chạy qua một test runner tự động để so sánh kết quả đầu ra với các bộ dữ liệu mẫu (test cases). Chỉ khi vượt qua tất cả bài test (`all test cases passed`), code mới được phép gộp vào nhánh chính.
- **Các khái niệm quan trọng:** Git Worktrees, Bare repository, Parallel branch directories, Automated Quality Control (QC), Test cases runner, CI/CD code validation.
- **Dạng nội dung:** Thực hành quản lý Git nâng cao và lập trình script kiểm thử tự động.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết thiết lập bare clone, khởi tạo worktree, và cách lập trình logic duyệt mảng test cases để gán kết quả True/False).

**Điểm nổi bật:**
- Kỹ thuật Git Worktrees là giải pháp cực kỳ thực tế giúp TA quản lý thời gian khi vừa phải code tính năng mới cho dự án tiếp theo, vừa phải nóng sửa lỗi (hotfix) cho dự án đang chạy render.

**Điểm hạn chế / Thiếu sót:**
- Cách viết test runner bằng danh sách logic thủ công lồng trong file `all_test_cases_passed` hơi thô sơ so với việc sử dụng các framework chuyên dụng như `unittest` hoặc `pytest` trong Python.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA chuyên nghiệp hóa quy trình viết và test tool, hạn chế tối đa việc đẩy các phiên bản tool bị lỗi cú pháp lên server làm gián đoạn công việc của artist.

---

### 📄 File: 06_google_drive_tool_01.txt

**Chủ đề chính:**
- Vai trò của tự động hóa CI/CD trong các studio lớn để giảm thiểu sai sót của con người.
- Thiết lập hệ thống lưu trữ tài nguyên đám mây (Perforce Depots hoặc Google Drive).
- Quy trình kéo tài nguyên (asset ingestion) từ client/đối tác outsource vào máy chủ local.
- Triết lý **"No Blackboxing"** (Không dùng hộp đen): Hiểu rõ mã nguồn copy thay vì nhắm mắt sử dụng.
- Lập trình Python sử dụng thư viện `requests` để tải tệp tin từ liên kết chia sẻ Google Drive.
- Trích xuất ID tệp tin từ URL chia sẻ để gọi API tải xuống.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học bắt đầu bằng việc giải thích tại sao studio lớn cần tự động hóa QC bằng CI/CD: số lượng asset và code đẩy lên hàng ngày là quá khổng lồ để supervisor có thể duyệt thủ công. Giảng viên vẽ sơ đồ mô tả luồng dữ liệu khi các đối tác outsource gửi asset (qua Perforce hoặc Google Drive) và studio cần kéo về máy chủ nội bộ. Giảng viên cảnh báo về thói quen xấu "blackboxing" - sao chép code trên mạng mà không hiểu nguyên lý. Để bắt đầu xây dựng tool đồng bộ đám mây, giảng viên hướng dẫn viết script `gdowntest.py` sử dụng thư viện `requests` để tương tác trực tiếp với API của Google Drive, trích xuất ID của tệp từ URL chia sẻ và tải thành công tệp Alembic `BoxMesh.abc` về máy.
- **Các khái niệm quan trọng:** Ingestion pipeline, Perforce depots vs Cloud drive, requests library, File ID extraction, Google Drive API download endpoint, "No Blackboxing" philosophy.
- **Dạng nội dung:** Lý thuyết thiết kế hệ thống và thực hành gọi API HTTP trong Python.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cách phân tích đường dẫn URL chia sẻ của Google Drive, trích xuất ID tệp, và viết mã xử lý HTTP request để tải dữ liệu nhị phân).

**Điểm nổi bật:**
- Nhắc nhở đắt giá về triết lý "No Blackboxing": Luôn in ra và phân tích từng dòng lệnh để làm chủ hoàn toàn mã nguồn, đặc biệt khi viết các tool quan trọng cho pipeline.

**Điểm hạn chế / Thiếu sót:**
- Thư viện `requests` mặc định của Python không tự động cài đặt sẵn trên một số môi trường, học viên cần chạy `pip install requests` trước.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cơ sở để TA xây dựng các công cụ tự động đồng bộ hóa asset (textures, alembics, cache) giữa client/render farm và máy trạm của artist.

---

### 📄 File: 07_google_drive_tool_02 (1440p).txt

**Chủ đề chính:**
- Chuyển đổi mã nguồn prototype sang hướng đối tượng (OOP Class `CloudUtils`).
- Tổ chức siêu dữ liệu tài nguyên (metadata) bằng tệp cấu hình JSON `asset_info.json`.
- Thiết lập từ khóa và ánh xạ thông tin asset (ID, Name, Link, Author).
- Sử dụng thư viện `json` để nạp tệp cấu hình động (`json.load`).
- Lập trình vòng lặp tải hàng loạt tài nguyên từ Google Drive API theo danh sách cấu hình.
- Tự động gán phần mở rộng tệp tin (`.abc` cho Alembic) dựa trên metadata.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học nâng cấp mã nguồn tải file đơn lẻ ở phần 1 lên một công cụ quản lý thư viện asset chuẩn công nghiệp. Giảng viên đóng gói mã nguồn vào class `CloudUtils` và xây dựng phương thức `download(file_id, destination)`. Để quản lý thông tin của hàng ngàn asset động, giảng viên tạo một tệp tin cấu hình JSON `asset_info.json` chứa các cặp khóa-giá trị lưu trữ chi tiết: tên asset, link Google Drive, tác giả, và các định danh liên quan. Trong mã Python chính, chương trình sử dụng khối lệnh `with open(...) as file:` để đọc tệp JSON này, lặp qua tất cả phần tử và tự động gọi phương thức `download` từ class `CloudUtils` để tải hàng loạt các tệp Alembic (`.abc`) về thư mục lưu trữ chung trên đĩa đám mây (mô phỏng server iCloud/Local của công ty).
- **Các khái niệm quan trọng:** OOP encapsulation, `CloudUtils` class, JSON metadata configuration, `json.loads` vs `json.load`, Batch downloading logic, Asset indexing.
- **Dạng nội dung:** Thực hành lập trình hướng đối tượng và quản lý cấu trúc dữ liệu JSON.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cách thiết lập class, cách gán tham chiếu `self` cho các phương thức con, và cách phân tích cú pháp tệp JSON phức tạp).

**Điểm nổi bật:**
- Việc sử dụng tệp JSON bên ngoài để cấu hình danh sách asset giúp công cụ linh hoạt tối đa: artist chỉ cần cập nhật link trong file JSON mà không cần mở hoặc chỉnh sửa bất kỳ dòng code Python nào của tool.

**Điểm hạn chế / Thiếu sót:**
- JSON file không hỗ trợ comment, gây khó khăn nếu studio muốn chú thích các dòng link asset trong tệp cấu hình này.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là mô hình chuẩn để thiết kế các asset loader/manager trong studio, kết nối trực tiếp cơ sở dữ liệu (JSON/Database) với các công cụ DCC như Houdini.

---

### 📄 File: 08_google_drive_tool_03.txt

**Chủ đề chính:**
- Quy trình tự động hóa kiểm định chất lượng (QC) đối với các file tải về.
- Nhận diện các lỗi dữ liệu phổ biến: file bị lỗi/hỏng (0 bytes) hoặc lỗi đường dẫn API.
- Tích hợp kiểm thử tự động (Unit Test cases) vào quy trình đẩy code lên Git.
- Xây dựng kịch bản kiểm thử giả lập (QC scenario) cho thuộc tính hình học (polygon budget).
- Tạo luồng logic kiểm định toàn cục (Boolean aggregation: all tests passed).

**Nội dung chi tiết:**
- **Tóm tắt:** Bổ sung bước kiểm định chất lượng (QC) để hoàn thiện công cụ kéo asset. Giảng viên giải thích rằng trong thực tế, các asset tải từ đám mây có thể bị lỗi mạng dẫn đến tệp tin rỗng ( dung lượng 0 bytes) hoặc sai thông tin vendor. Vì vậy, ta cần viết các đoạn mã kiểm tra (QC scripts) để kiểm định file trước khi đưa vào server nội bộ. Để minh họa, giảng viên viết một script chạy các test case kiểm tra độ chính xác của thuật toán tìm kiếm trên mảng. Nếu một test case thất bại (ví dụ trả về chỉ mục sai), hệ thống sẽ báo `fail` và không cho phép deploy code. Giảng viên cũng lấy ví dụ về việc QC hình học trong VFX: nếu file hình học do artist tạo ra vượt quá giới hạn số lượng polygon (poly count budget) quy định của dự án, test case QC sẽ báo thất bại và yêu cầu artist làm sạch lại lưới trước khi xuất bản.
- **Các khái niệm quan trọng:** File size validation (0 bytes checks), Automated QC gates, Unit testing logic, Polygon budget checks, Boolean check array.
- **Dạng nội dung:** Tư duy thiết kế QC hệ thống và thực hành viết code kiểm tra logic.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Phân tích chi tiết quy trình QC tự động và hướng dẫn viết hàm kiểm thử logic trả về mảng Boolean để quyết định quyền deploy).

**Điểm nổi bật:**
- Đưa ra giải pháp QC tự động về mặt dung lượng file và polycount hình học giúp lọc bỏ sớm các asset lỗi trước khi chúng đi vào pipeline chính, giúp tiết kiệm hàng trăm giờ render bị hỏng vô ích.

**Điểm hạn chế / Thiếu sót:**
- Ví dụ kiểm thử trong file chủ yếu minh họa bằng thuật toán Binary Search, chưa đính kèm code thực tế đọc thông tin số lượng polygon của file Alembic vừa tải về.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Xây dựng các cổng QC tự động (automated QC gates) để kiểm tra lưới hình học, UV, textures trước khi publish là nhiệm vụ tối quan trọng của TA để giữ pipeline hoạt động trơn tru.

---

### 📄 File: 09_system_design.txt

**Chủ đề chính:**
- Kiến trúc Client - Server và giao thức kết nối (HTTP, IP, Ports).
- Phân tích hiệu năng hệ thống thông qua Latency (Độ trễ) và Throughput (Băng thông/Sản lượng).
- Độ sẵn sàng của hệ thống (Availability) tính bằng số lượng "chữ số 9" (99% vs 99.999% - Five Nines).
- Các cơ chế tăng cường độ tin cậy: Redundancy (Dự phòng) và Caching (Bộ nhớ đệm).
- Cơ chế Load Balancer (Bộ cân bằng tải) và các thuật toán băm (Round-robin, Hashing).
- Cơ chế Leader Election quản lý lỗi hệ thống và các loại hình lưu trữ dữ liệu lớn (Blob storage vs Key-value).

**Nội dung chi tiết:**
- **Tóm tắt:** File này là một bài giảng lý thuyết toàn diện về kiến trúc hệ thống (System Design). Giảng viên giải thích các thành phần cốt lõi của một hệ thống mạng lớn (từ Client gửi request qua Load Balancer đến các Web/Application/Cache server). Bài học đi qua các khái niệm đo lường hiệu năng như Latency và Throughput, định nghĩa độ khả dụng Availability và giải thích tại sao mức 99% (Two Nines) vẫn cực kỳ nguy hiểm (gây gián đoạn hàng chục giờ mỗi năm), đòi hỏi hệ thống chuẩn phải đạt 99.999% (Five Nines). Giảng viên cũng phân tích các kỹ thuật quản lý phân tán như chia nhỏ dữ liệu lớn (sharding/partitioning), bầu chọn máy chủ trưởng (leader election), dự phòng (redundancy) để hệ thống tự phục hồi khi có máy chủ bị hỏng đột ngột, và phân biệt Blob Storage (như Amazon S3, Google Cloud Storage chuyên chứa file nặng như 3D mesh, texture) với Key-Value pair storage chứa metadata gọn nhẹ.
- **Các khái niệm quan trọng:** Client-Server model, Latency & Throughput, High Availability (nines), Redundancy, Caching topology, Load Balancer, Blob storage (S3/GCS), Leader Election, Vertical vs Horizontal scaling.
- **Dạng nội dung:** Lý thuyết nền tảng về thiết kế kiến trúc hệ thống.

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rất rộng và dễ hiểu các thuật ngữ cốt lõi của System Design nhưng không đi sâu vào code cài đặt máy chủ).

**Điểm nổi bật:**
- Giải thích cơ chế Caching cực kỳ trực quan thông qua ví dụ game Call of Duty: Khi game load trang bị/avatar của người chơi, hệ thống sẽ đọc từ một cache point được chuẩn bị sẵn thay vì truy vấn và tính toán lại từ các file mesh/texture gốc từ đầu, giúp tăng tốc độ tải màn chơi.

**Điểm hạn chế / Thiếu sót:**
- Không cung cấp code Python hoặc cấu hình server mẫu để minh họa cho các cơ chế phức tạp như Load Balancer hay Leader Election.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA hiểu cách thức vận hành của hạ tầng IT studio (Render Farm, Asset Management Servers, Cloud Storage). Nắm vững System Design giúp TA đưa ra thiết kế pipeline chính xác, biết đặt cache đúng chỗ để tránh tắc nghẽn băng thông mạng studio.

---

### 📄 File: 10_pipeline_01.txt

**Chủ đề chính:**
- Khái niệm và vai trò của Pipeline trong studio VFX/Game.
- Quản lý kênh giao tiếp giữa các bộ phận (Artist, Technical Artist, Developer, Production).
- Cấu trúc cốt lõi của Pipeline: Core API hub (cơ sở dữ liệu/API server) và giao diện đồ họa (UI).
- Phân quyền hạn truy cập (Access restrictions) dựa trên vai trò seniority trong công việc.
- Ứng dụng cấu trúc dữ liệu Ngăn xếp (Stack) để quản lý phiên bản asset (Versioning).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu triết lý xây dựng pipeline sản xuất đồ họa. Trong một studio lớn, việc giao tiếp và chuyển giao hàng ngàn tệp tin giữa các tổ nghệ sĩ, TA và đạo diễn sẽ trở nên hỗn loạn nếu thiếu một quy trình chuẩn hóa. Pipeline đóng vai trò là kênh giao tiếp trung tâm, được xây dựng dựa trên một core API hub ở backend kết hợp với giao diện UI thân thiện ở frontend. Hệ thống sẽ áp dụng phân quyền nghiêm ngặt: các supervisor có toàn quyền chỉnh sửa/xóa dữ liệu, trong khi artist thông thường chỉ có quyền đọc và xuất bản (publish). Giảng viên giới thiệu cấu trúc dữ liệu Stack (Ngăn xếp) để quản lý phiên bản: mỗi lần artist publish, một phiên bản mới (v001, v002) được đẩy (push) lên đỉnh của stack. Khi các bộ phận khác truy vấn, họ sẽ luôn lấy phiên bản mới nhất từ đỉnh ngăn xếp, nhưng vẫn có thể dễ dàng lấy lại các phiên bản cũ bên dưới nếu phiên bản mới gặp lỗi.
- **Các khái niệm quan trọng:** VFX Pipeline, Core API hub, Access control, File publishing, Versioning stack, LIFO (Last In First Out) query.
- **Dạng nội dung:** Lý thuyết quy trình sản xuất đồ họa.

**Mức độ sâu:**
- 🟡 Trung bình (Cung cấp tư duy kiến trúc và quy trình trao đổi file tiêu chuẩn trong studio lớn, chưa đi vào code Python).

**Điểm nổi bật:**
- Giải thích rõ tại sao việc giữ lại lịch sử các phiên bản cũ trong "ngăn xếp" (stack) lại vô cùng quan trọng: Nó cung cấp một phao cứu sinh (rollback path) giúp studio nhanh chóng khôi phục công việc khi phiên bản mới nhất của asset bị hỏng.

**Điểm hạn chế / Thiếu sót:**
- Không hướng dẫn chi tiết cách viết code Python để tạo cấu trúc stack lưu file trên ổ cứng.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – TA là người trực tiếp xây dựng hoặc bảo trì pipeline này. Hiểu rõ kiến trúc API hub và quản lý phiên bản là nền tảng để TA thiết kế các tool import/export asset cho nghệ sĩ.

---

### 📄 File: 11_encapsulation_properties.txt

**Chủ đề chính:**
- Khái niệm tính đóng gói (Encapsulation) trong lập trình hướng đối tượng (OOP).
- Ba loại công cụ bổ trợ truy cập (Access Modifiers): Public, Protected (`_`), Private (`__`).
- Cách thức bảo vệ dữ liệu trong class nhạy cảm (passport number, salary, asset IDs).
- Sử dụng bộ trang trí `@property` làm Getter trong Python.
- Thiết lập Setter (`@<property>.setter`) và Deleter (`@<property>.deleter`) để quản lý thuộc tính.
- Áp dụng đóng gói để xây dựng cấu trúc lớp đối tượng Employee và quản lý tài khoản.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học cung cấp kiến thức nền tảng về Encapsulation (tính đóng gói) và Property Decorators trong Python. Lập trình viên học cách sử dụng các tiền tố dấu gạch dưới để kiểm soát quyền truy cập thuộc tính trong một lớp: public (mặc định), protected (bắt đầu bằng `_`, chỉ dùng trong class và class kế thừa), và private (bắt đầu bằng `__`, chỉ truy cập được bên trong class đó thông qua cơ chế mangling). Giảng viên hướng dẫn viết class `Employee` với các thuộc tính như tên, tuổi, vị trí.
- Tiếp theo, giảng viên hướng dẫn viết bộ trang trí `@property` để chuyển đổi phương thức `full_name()` thành một thuộc tính có thể đọc trực tiếp (getter) mà không cần dấu ngoặc tròn. Học viên cũng học cách thiết lập setter để tự động tách chuỗi họ và tên khi người dùng gán giá trị mới cho thuộc tính `full_name = "First Last"`, giúp chuẩn hóa dữ liệu đầu vào.
- **Các khái niệm quan trọng:** OOP Encapsulation, Public/Protected/Private modifiers, Python double underscore mangling, `@property` decorator (getter), Setter and Deleter methods.
- **Dạng nội dung:** Thực hành lập trình Python OOP nâng cao.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cú pháp viết getter, setter, deleter, cơ chế name mangling của private variable và kế thừa class).

**Điểm nổi bật:**
- Nhấn mạnh tầm quan trọng của việc ẩn giấu các biến nhạy cảm và các helper function của class thông qua Protected/Private để tránh việc các lập trình viên khác trong team vô tình sửa đổi trực tiếp dữ liệu bên trong làm hỏng trạng thái class.

**Điểm hạn chế / Thiếu sót:**
- Ví dụ minh họa sử dụng các lớp nhân viên (Employee) khá phổ biến, chưa lồng ghép các lớp đối tượng VFX cụ thể (như Geometry, Mesh, Point Cloud).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Khi viết các API hoặc tool dùng chung cho cả studio, TA cần đóng gói mã nguồn cực kỳ cẩn thận. Việc phơi bày quá nhiều biến public sẽ khiến code dễ bị lỗi khi các artist hoặc TA khác gọi sai cách.

---

### 📄 File: 12_yaml_data.txt

**Chủ đề chính:**
- Quản lý thông tin nhân sự và tích hợp hệ thống dữ liệu YAML.
- Sử dụng thư viện `PyYAML` để nạp dữ liệu cấu hình thông qua `yaml.safe_load()`.
- Chuyển đổi dữ liệu YAML thô thành cấu trúc Hash Table / Dictionary trong Python.
- Kỹ thuật Dictionary Comprehension để tối ưu hóa ánh xạ phòng ban và người quản lý.
- Áp dụng OOP: Sử dụng class `Employee` và `@property` để tự động tạo email và gán line manager.
- Xuất bản dữ liệu tổng hợp ra tệp tin cấu hình JSON `user_data.json` có định dạng.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học hướng dẫn thực hành một bài toán tích hợp dữ liệu thực tế: Đọc thông tin các nhân viên mới từ file `employees.yaml` và thông tin quản lý phòng ban từ file `line_managers.yaml` để tạo ra một cơ sở dữ liệu JSON thống nhất. Đầu tiên, chương trình sử dụng thư viện `PyYAML` với hàm `yaml.safe_load(file)` để chuyển đổi tệp YAML thành dictionary trong Python. Tiếp theo, giảng viên viết một lệnh Dictionary Comprehension để lập bản đồ quản lý theo phòng ban (`manager_dict = {managers[m]['department']: managers[m]['name'] for m in managers}`).
- Sau đó, chương trình lặp qua danh sách nhân viên mới, khởi tạo đối tượng `Employee`, sử dụng thuộc tính `@property` để tự động sinh email công ty dạng `first.last@company.com`. Đồng thời, chương trình đối chiếu phòng ban của nhân viên để tự động gán tên line manager tương ứng (bỏ qua nếu nhân viên đó đã có vai trò là line manager). Cuối cùng, toàn bộ dữ liệu phong phú này được lưu xuống file `user_data.json` bằng `json.dump()`.
- **Các khái niệm quan trọng:** PyYAML library, `yaml.safe_load()`, Dictionary Comprehension, Metadata aggregation, email generation, conditional line manager assignment, JSON formatting (`indent`).
- **Dạng nội dung:** Thực hành tích hợp dữ liệu, thao tác file YAML/JSON và Python OOP.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết viết mã đọc file, xử lý chuỗi họ tên, cấu trúc hóa dictionary lồng và xuất file JSON hoàn chỉnh).

**Điểm nổi bật:**
- Nhấn mạnh triết lý: Dù có thể xử lý việc gộp dữ liệu bằng một vài dòng code thô sơ, nhưng việc xây dựng cấu trúc Class rõ ràng mang lại khả năng mở rộng (scalability) vượt trội, giúp hệ thống dễ dàng bảo trì khi công ty scale lên hàng ngàn nhân viên.

**Điểm hạn chế / Thiếu sót:**
- PyYAML không được tích hợp mặc định trong Python chuẩn, học viên cần chạy `pip install pyyaml` trong conda environment của mình để chạy mã.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – YAML là định dạng tệp cấu hình phổ biến nhất trong các công cụ VFX và game (như Unity, Unreal, Houdini configs). Việc nắm vững cách thao tác với YAML và chuyển đổi nó sang JSON là bắt buộc đối với TA để viết các tool cấu hình môi trường hoặc thiết lập pipeline.

---

### 📄 File: 13_houdini_packages_and_shell_script_01.txt

**Chủ đề chính:**
- Phân tích nhược điểm của việc cấu hình môi trường bằng tệp `houdini.env` truyền thống.
- Giới thiệu cơ chế **Houdini Packages** dưới dạng tệp tin cấu hình JSON.
- Tự động hóa tạo file package JSON bằng Python (`create_package_json.py`).
- Sử dụng thư viện `os.getlogin()` để nhận diện định danh người dùng hệ thống.
- Đối chiếu người dùng hiện tại với cơ sở dữ liệu `user_data.json` để lấy ID nhân viên.
- Dynamically gán các biến môi trường (`USER_ID`) vào session của Houdini thông qua cấu trúc package.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học chuyển hướng sang việc thiết lập cấu hình môi trường chạy Houdini chuyên nghiệp. Giảng viên chỉ ra rằng việc ghi đè trực tiếp vào file `houdini.env` của nghệ sĩ rất dễ gây lỗi hệ thống và không thể quản lý tập trung. Thay vào đó, Houdini cung cấp tính năng **Packages** – đọc các tệp JSON nằm trong thư mục `packages/` để tự động nạp các biến môi trường và đường dẫn công cụ khi khởi động.
- Để tự động hóa, giảng viên viết script `create_package_json.py`. Script này dùng lệnh `os.getlogin()` để lấy tên tài khoản OS của máy trạm hiện tại, đối chiếu với cơ sở dữ liệu nhân viên `user_data.json` để tìm thông tin khớp, trích xuất ID nhân viên, và tự động sinh ra một file package JSON đặt tên là `company_vars.json`. File JSON này chứa cú pháp cấu hình môi trường đặt biến `USER_ID` tương ứng với ID của người dùng đó. Biến này sẽ được dùng để tag tên artist khi xuất bản asset sau này.
- **Các khái niệm quan trọng:** Houdini Packages, Environment JSON structure, `os.getlogin()`, ID database lookup, Dynamic environment injection, `company_vars.json`.
- **Dạng nội dung:** Quản lý hệ thống phát triển và tích hợp môi trường Houdini.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cấu trúc JSON hợp lệ của Houdini Packages và cách dùng Python để viết tệp cấu hình tự động dựa trên định danh OS).

**Điểm nổi bật:**
- Giới thiệu cơ chế Houdini Packages thay thế hoàn toàn cho `houdini.env`, giúp các studio dễ dàng phân phối các bộ công cụ (HDA, shelf, plugins) cho hàng trăm máy trạm một cách độc lập và sạch sẽ.

**Điểm hạn chế / Thiếu sót:**
- Lệnh `os.getlogin()` có thể trả về lỗi trên một số môi trường chạy terminal headless hoặc server render farm không có phiên đăng nhập trực quan, trong thực tế thường dùng `getpass.getuser()` thay thế.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Kỹ năng cấu hình Houdini Packages là bắt buộc đối với một Pipeline TA để phân phối các công cụ tự phát triển trong studio đến máy tính của artist một cách tự động và ổn định.

---

### 📄 File: 14_houdini_packages_and_shell_script_02.txt

**Chủ đề chính:**
- Tự động hóa toàn bộ chuỗi công việc bằng shell script (`integrate_employee.sh`).
- Cấu hình executor dòng lệnh với cú pháp shebang `#!/bin/bash`.
- Tự động hóa liên tiếp: Tích hợp nhân sự -> Sinh file package JSON -> Sao chép file package vào thư mục Houdini.
- Quản lý phân quyền thực thi tệp tin trên hệ điều hành bằng lệnh `chmod +x`.
- Xác thực kết quả: Kiểm tra biến môi trường `USER_ID` được nạp tự động trong phiên Houdini.
- Truy vấn biến môi trường trong Python của Houdini thông qua `os.environ.get("USER_ID")`.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học liên kết tất cả các script đã viết thành một hệ thống tự động hoàn chỉnh thông qua một tệp shell script (`.sh`). Giảng viên viết script `integrate_employee.sh` sử dụng trình thực thi bash (`#!/bin/bash`). Shell script này sẽ tự động chạy: Đầu tiên là `system_integration.py` để xử lý YAML và tạo JSON nhân sự; Tiếp theo chạy `create_package_json.py` để tạo file package của Houdini; Cuối cùng thực hiện lệnh sao chép `cp` để đưa file package JSON này trực tiếp vào thư mục `packages/` trong preferences của Houdini trên máy trạm.
- Học viên học cách dùng lệnh `chmod +x integrate_employee.sh` để cấp quyền chạy cho tệp script. Để kiểm chứng, giảng viên mở Houdini, kiểm tra bảng Help -> About -> Show Details và xác nhận biến môi trường `USER_ID` đã được Houdini tự động nạp thành công ở startup. Cuối cùng, thực hiện gọi `os.environ.get("USER_ID")` trong Houdini Python Shell để xác thực mã nguồn Python đã nhận biết được biến môi trường này.
- **Các khái niệm quan trọng:** Shell Scripting, Shebang header, Command execution order, File permissions (`chmod +x`), Preferences directory mapping, Startup environment validation.
- **Dạng nội dung:** Quản lý hệ thống phát triển, lập trình shell script và cấu hình Houdini.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết các lệnh shell, quản lý đường dẫn thư mục hệ thống và cách kiểm tra chéo các biến môi trường trực tiếp trong Houdini).

**Điểm nổi bật:**
- Thay thế hoàn toàn quy trình nạp thủ công bằng một file script chạy "một click" duy nhất, mô phỏng chính xác cách thức các studio lớn đồng bộ môi trường máy trạm của artist mỗi khi bắt đầu ngày làm việc.

**Điểm hạn chế / Thiếu sót:**
- Shell script `.sh` mặc định chỉ chạy trên Linux/macOS. Đối với hệ điều hành Windows, học viên sẽ phải viết tệp batch `.bat` hoặc sử dụng PowerShell `.ps1` để thực hiện các thao tác tương tự (sử dụng lệnh `copy` thay cho `cp`).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – TA thường xuyên phải viết các script khởi chạy (launcher scripts) cho artist để tự động đồng bộ plugin và cấu hình dự án trước khi mở phần mềm.

---

### 📄 File: 15_publisher_node_01.txt

**Chủ đề chính:**
- Thiết kế prototype cho công cụ xuất bản hình học (Publisher Node) dưới dạng Subnetwork.
- Tích hợp node `filecache` SOP bên trong subnet để xử lý việc lưu tệp tin.
- Expose (phơi bày) các tham số của node filecache ra giao diện ngoài của main subnet.
- Sử dụng hàm `hou.expandString()` để giải quyết các đường dẫn chứa biến môi trường (như `$HIP`, `$JOB`).
- Thuật toán tự động tăng phiên bản (Auto-versioning): Duyệt thư mục đích để tìm phiên bản cao nhất.
- Tạo cấu trúc thư mục tự động trên đĩa trước khi xuất bản hình học để tránh lỗi cook.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học bắt đầu xây dựng công cụ Publisher Node trong Houdini. Công cụ này được thiết kế dưới dạng subnet để đảm bảo tính gọn gàng. Bên trong subnet, giảng viên đặt một node `filecache` SOP để thực hiện ghi tệp hình học. Giảng viên sử dụng Edit Parameter Interface để dọn dẹp các tham số mặc định của subnet và kéo các tham số điều khiển của node filecache (như nút Save to Disk, trường File Path) ra giao diện ngoài để artist dễ tương tác.
- Để tự động hóa việc lưu, giảng viên viết một script Python đính vào nút "Set Path". Script sử dụng `hou.expandString()` để giải quyết các biến môi trường trong đường dẫn nhập vào, trích xuất thư mục cha, kiểm tra xem thư mục đó có tồn tại hay không. Nếu thư mục đã chứa các file cache phiên bản cũ (như `v001`, `v002`), script sẽ tự động tính toán và đặt tên phiên bản tiếp theo là `v003`. Cuối cùng, script tự tạo thư mục trên đĩa (nếu chưa có) và cập nhật đường dẫn lưu tệp của node.
- **Các khái niệm quan trọng:** Publisher SOP prototype, File Cache wrapping, Parameter promotion, `hou.expandString()`, Directory scanning, Auto-versioning index calculation, Folder creation (`os.makedirs`).
- **Dạng nội dung:** Thực hành lập trình Houdini Python API và thiết kế HDA.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cách viết script Python tương tác với hình học Houdini, xử lý đường dẫn tương đối và tự động hóa thuật toán tìm phiên bản trống tiếp theo trên đĩa).

**Điểm nổi bật:**
- Giải thuật tự động tìm phiên bản tiếp theo (Auto-versioning) giúp ngăn chặn lỗi phổ biến của artist: Vô tình ghi đè lên các file cache cũ của đồng nghiệp hoặc của chính mình, đảm bảo lịch sử phiên bản luôn được bảo toàn.

**Điểm hạn chế / Thiếu sót:**
- Code prototype được viết trực tiếp vào một tham số string tạm thời trên node, chưa đóng gói hoàn toàn vào PythonModule của HDA.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Xây dựng tool publish/cache là công việc kinh điển nhất của một Pipeline TA, giúp chuẩn hóa định dạng đặt tên file và đường dẫn lưu trữ của toàn bộ dự án.

---

### 📄 File: 16_publisher_node_02.txt

**Chủ đề chính:**
- Thiết kế công cụ bổ trợ: **Asset Loader Node** để tải các file đã publish.
- Sử dụng tham số loại `File Directory` để trỏ vào thư mục chứa các phiên bản cache.
- Sử dụng **Menu Script** để tự động điền danh sách phiên bản vào dropdown menu.
- Cú pháp Menu Script trong Houdini: Trả về danh sách chuỗi dạng cặp `[Token, Label]`.
- Đồng bộ hóa: Chọn phiên bản trên menu -> Tự động cập nhật đường dẫn của node `file` SOP bên trong.
- Ứng dụng hàm `menuLabels()` của tham số để trích xuất tên file cụ thể tương ứng với chỉ mục.

**Nội dung chi tiết:**
- **Tóm tắt:** Bổ sung công cụ Asset Loader để artist tải và duyệt các phiên bản cache hình học đã xuất bản từ Publisher Node. Node Loader là một subnet chứa một node `file` SOP bên trong. Trên giao diện, Loader expose một trường chọn thư mục `Assets Folder` và một dropdown menu `Version`. Để menu này tự động hiển thị danh sách các tệp cache có sẵn trong thư mục, giảng viên hướng dẫn viết một **Menu Script** bằng Python.
- Theo quy định của Houdini, Menu Script phải trả về một danh sách chuỗi chứa các cặp Token (giá trị nội bộ) và Label (chữ hiển thị trên giao diện). Script sử dụng `os.listdir()` để quét thư mục, dùng `enumerate()` để lấy chỉ mục làm Token và tên file làm Label. Khi artist thay đổi lựa chọn trên dropdown menu, một callback script sẽ tự động kích hoạt, lấy tên file tương ứng từ chỉ mục đã chọn thông qua `menuLabels()`, kết hợp với đường dẫn thư mục để cập nhật đường dẫn nạp file cho node `file` SOP bên trong, giúp artist chuyển đổi mượt mà giữa các phiên bản asset.
- **Các khái niệm quan trọng:** Asset Loader SOP, Directory parameter, Menu Script, Token-Label array, `os.listdir()`, Dropdown callback script, `menuLabels()` index mapping.
- **Dạng nội dung:** Lập trình UI động và đồng bộ hóa node trong Houdini.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cách viết Menu Script, giải thích kỹ cơ chế Token-Label và cách đồng bộ hóa giá trị giữa giao diện ngoài và node file SOP bên trong).

**Điểm nổi bật:**
- Kỹ thuật viết Menu Script giúp giao diện của Houdini trở nên cực kỳ linh hoạt và chuyên nghiệp: Danh sách phiên bản tự động cập nhật theo thời gian thực dựa trên các file thực tế đang có trên đĩa cứng của server mà không cần hard-code.

**Điểm hạn chế / Thiếu sót:**
- Menu Script quét thư mục đĩa trực tiếp mỗi lần người dùng click vào dropdown. Nếu thư mục chứa hàng chục ngàn file trên ổ đĩa mạng (network drive) chậm, việc này có thể gây đứng hình Houdini tạm thời (cần cơ chế caching kết quả quét).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Thiết kế giao diện động (dynamic UI) và viết Menu Script là kỹ năng nâng cao rất quan trọng của TA để tạo ra các công cụ dễ sử dụng, trực quan cho nghệ sĩ trong studio.

---

### 📄 File: 17_assignment.txt

**Chủ đề chính:**
- Đề bài tập thực hành tổng hợp của Week 03.
- Yêu cầu xây dựng một HDA lưu trữ toàn bộ code logic trên một kho chứa Git (GitHub Repo).
- Houdini HDA phải nạp mã nguồn chạy trực tiếp từ bản clone của GitHub Repo đó.
- Tính năng của HDA: Tải hình học đầu vào (như Box/Sphere) và tự động upload lên Google Drive.
- Kết quả nộp bài: Link GitHub chứa mã nguồn và Link Google Drive chứa asset đã được upload thành công.
- Mục tiêu: Chứng minh khả năng vận hành trọn vẹn của hệ thống pipeline kết nối đám mây.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài tập thực hành tuần 03 yêu cầu học viên tích hợp tất cả các kiến thức đã học thành một hệ thống thực tế. Học viên phải tạo một kho chứa trên GitHub để quản lý toàn bộ mã nguồn Python phát triển công cụ. HDA trong Houdini sẽ được cấu hình để nạp code trực tiếp từ kho chứa Git này (thay vì embed code trong HDA).
- Khi chạy, công cụ này sẽ lấy hình học đầu vào (ví dụ một node Box hoặc Sphere), thực hiện ghi cache và tự động gọi API để upload file này lên thư mục Google Drive chung của dự án. Học viên nộp bài bằng cách gửi link GitHub chứa mã nguồn sạch (đã refactor) và link tệp tin đã upload thành công trên Google Drive để chứng minh luồng hoạt động từ xa.
- **Các khái niệm quan trọng:** Git-driven HDA, External code loading, Google Drive API upload integration, Geometry exporter, Pipeline round-trip.
- **Dạng nội dung:** Đề bài tập thực hành tổng hợp.

**Mức độ sâu:**
- 🟡 Trung bình (Mô tả yêu cầu thiết kế hệ thống và tiêu chí đánh giá, không có code giải mẫu).

**Điểm nổi bật:**
- Bài tập mang tính thực chiến cực cao, mô phỏng chính xác công việc của một Pipeline Developer trong studio: Viết code quản lý trên Git, nạp code động vào DCC (Houdini) và đẩy kết quả hình học lên hệ thống lưu trữ đám mây.

**Điểm hạn chế / Thiếu sót:**
- Đề bài không hướng dẫn chi tiết cách thiết lập xác thực (Authentication/OAuth2) với Google Drive API để upload file, học viên phải tự nghiên cứu cơ chế bảo mật này.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là bài tập hoàn hảo giúp TA nâng tầm từ một người viết script Houdini đơn thuần thành một Pipeline Engineer có khả năng thiết kế các giải pháp tích hợp đám mây hiện đại.

---

# 3. Weekly Summary (Tổng kết Week 03)

### 3.1. Kiến thức cốt lõi đã học
1. **DevOps & CI/CD trong Sản xuất:**
   - Hiểu bản chất vòng lặp vô hạn của phát triển phần mềm/pipeline và so sánh trực quan với quy trình sản xuất shot VFX và huấn luyện mô hình MLOps.
   - Thiết kế các bộ kiểm thử tự động (QC) trên Git trước khi deploy để kiểm soát chất lượng file (0 bytes, polycount budget).
2. **Quản lý phiên bản Git nâng cao:**
   - Làm chủ quy trình Forking và đồng bộ hóa upstream để phối hợp làm việc trên các thư viện nguồn mở hoặc dự án liên studio.
   - Ứng dụng **Git Worktrees** bằng cách clone bare repository để làm việc song song trên nhiều nhánh độc lập dưới dạng các thư mục ổ đĩa, loại bỏ việc stash code.
3. **Kết nối API Đám mây & Siêu dữ liệu:**
   - Viết class `CloudUtils` tương tác với Google Drive API để tải tệp Alembic.
   - Quản lý cấu hình danh sách tài nguyên tập trung bằng tệp JSON (`asset_info.json`), tách biệt dữ liệu với logic mã nguồn.
4. **Kiến trúc hệ thống (System Design):**
   - Nắm vững các khái niệm Clients, Servers, Latency, Throughput, Caching, Load Balancers.
   - Phân biệt Blob storage (AWS S3/Google Cloud Storage) chứa file nặng và Key-value storage chứa metadata. Hiểu cơ chế Sharding và Leader Election.
5. **Python OOP & Tích hợp Môi trường:**
   - Tính đóng gói Encapsulation (Public, Protected, Private) và sử dụng bộ trang trí `@property` (Getters, Setters, Deleters) để bảo vệ dữ liệu lớp Employee.
   - Đọc/ghi cấu hình tệp YAML và tự động sinh file cấu hình **Houdini Packages** JSON (`company_vars.json`).
   - Viết shell script (`.sh`) để tự động hóa toàn bộ quy trình tích hợp môi trường từ một lệnh chạy duy nhất.
6. **Houdini Python API & UI nâng cao:**
   - Xây dựng **Publisher Node** tự động hóa việc cache hình học và tính toán số phiên bản tự động tăng (Auto-versioning) trên đĩa cứng.
   - Xây dựng **Asset Loader Node** tích hợp **Menu Script** bằng Python để hiển thị danh sách file cache động dưới dạng dropdown menu cho artist chọn lựa.

### 3.2. Dự án & Bài tập đã thực hiện
- **Dự án Hệ thống Tải tài nguyên đám mây:** Viết công cụ Python dạng Class kết hợp file JSON cấu hình để tự động tải hàng loạt tệp Alembic từ Google Drive về máy chủ iCloud.
- **Hệ thống Tự động hóa Phân phối Tool:** Viết shell script tự động tích hợp thông tin nhân sự từ YAML, sinh file Houdini Package JSON và copy vào hệ thống để nạp biến môi trường `USER_ID` tự động khi artist mở Houdini.
- **Dự án Publisher & Loader Node:** Thiết kế bộ đôi công cụ xuất bản hình học (tự tạo folder, tự tăng phiên bản cache) và nạp hình học động (dùng Menu Script liệt kê file đĩa để artist chọn phiên bản tải lên).

---

### 📂 Cập nhật tiến độ của Agent:
1. Tôi đã tạo và ghi toàn bộ dữ liệu phân tích chi tiết của Week 03 vào file báo cáo [week_03_report.md](file:///j:/DOWNLOAD/COURSES/Rebelway%20-%20Python%20For%20Production/week_03/week_03_report.md) trong thư mục `week_03`.
2. Đã cập nhật lịch sử thay đổi của dự án trong tệp tin guidelines [AGENTS.md](file:///j:/DOWNLOAD/COURSES/Rebelway%20-%20Python%20For%20Production/AGENTS.md).
