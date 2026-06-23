# Rebelway - Python For Production: Week 08 Report

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 12 file (bao gồm các bài học lý thuyết về kiến trúc phần cứng GPU, tự lập trình GPU Kernel bằng Numba, thiết kế API bằng FastAPI/Uvicorn, nền tảng LLMs/Transformers, Prompt Engineering & Fine-tuning, tích hợp AI API (Mistral/Llama) và Stable Diffusion sinh texture tự động trong Houdini, các khái niệm triển khai Deployment/DevOps, thuật toán thực hành phỏng vấn LeetCode và hướng dẫn làm bài tập lớn cuối khóa).
- **Chủ đề chính của tuần:**
  - **Kiến trúc phần cứng & Lập trình GPU Kernel:** Tìm hiểu về sự khác biệt giữa CPU và GPU, cấu trúc hệ thống phân cấp xử lý song song của GPU (Grid, Block, Thread). Tự lập trình một GPU Kernel nhân ma trận bằng Python sử dụng thư viện Numba (`numba.cuda`) kết hợp quản lý bộ nhớ chia sẻ (Shared Memory) để tăng tốc độ xử lý lên hàng nghìn lần so với CPU.
  - **Thiết kế API (FastAPI & Uvicorn):** Tìm hiểu khái niệm API và các mô hình thiết kế Web API (REST, SOAP, GraphQL). Thực hành xây dựng một API server cục bộ bằng FastAPI và chạy bằng Uvicorn, cấu hình các route với path parameters và query parameters, viết client script kiểm thử bằng thư viện `requests`.
  - Nền tảng Mô hình Ngôn ngữ lớn (LLMs & Transformers):** Tìm hiểu lịch sử từ RNNs (Recurrent Neural Networks) với hạn chế bộ nhớ tuần tự sang kiến trúc Transformers hiện đại sử dụng cơ chế tự chú ý (Self-Attention) và các đầu chú ý (Attention Heads) chạy song song hiệu quả. Phân biệt các mô hình Encoder-only (BERT), Decoder-only (GPT) và Encoder-Decoder (T5).
  - **Prompt Engineering & Fine-tuning:** Phân biệt In-Context Learning (Zero-shot, One-shot, Few-shot) trong cửa sổ ngữ cảnh (Context Window) với Fine-tuning mô hình (Full Fine-tuning vs PEFT/LoRA). Khảo sát các tham số điều chỉnh LLMs như `max_tokens`, `top_k`, `top_p` và `temperature`.
  - **Tích hợp AI trong Houdini:** Xây dựng các shelf tools tương tác trong Houdini:
    - Llama AI Assistant: Sử dụng thư viện Replicate gọi Llama-2 trên cloud, tích hợp giao diện nhập liệu `hou.ui.readInput()` và prompt engineering hệ thống để hỗ trợ giải đáp các câu hỏi kỹ thuật chuyên sâu về Houdini (PDG, OSL, Material Networks).
    - AI Texture Generator: Sử dụng Stable Diffusion tạo texture tự động từ prompt của nghệ sĩ, tự động tối ưu hóa prompt bằng các từ khóa chất lượng ("high resolution, realistic, tileable"), tải ảnh qua `urllib.request` và gán tự động vào thuộc tính texture map của node shader.
  - **Tổng quan khái niệm Triển khai (Deployment & DevOps):** Khảo sát các công nghệ đóng gói và phân phối ứng dụng: Virtual environments, `requirements.txt`, `setup.py`, Containers (Docker), Container Orchestration (Kubernetes), PaaS (Heroku, Vercel, Next.js), ORM (Prisma & PostgreSQL), WebAssembly (WASM - "HTML is the new .exe"), PythonAnywhere, Serverless computing, và phân phối package qua PyPI.
  - **Thuật toán phỏng vấn kỹ thuật LeetCode:** Thực hành giải quyết các bài toán phỏng vấn kinh điển trên LeetCode bằng các kỹ thuật tối ưu hóa độ phức tạp thuật toán và bộ nhớ (Big O):
    - Two Sum: Tối ưu từ $O(N^2)$ xuống $O(N)$ bằng Hash Table (Python dictionary).
    - Three Sum: Tối ưu từ $O(N^3)$ xuống $O(N^2)$ bằng kỹ thuật hai con trỏ (Two Pointers) trên mảng đã sắp xếp.
    - Valid Palindrome: Kiểm tra chuỗi đối xứng tối ưu $O(N)$ thời gian và $O(1)$ bộ nhớ bằng hai con trỏ chạy từ hai đầu.
    - Longest Common Prefix: Tìm tiền tố chung dài nhất sử dụng kỹ thuật tìm từ ngắn nhất và thu hẹp tập hợp ký tự (Set intersection).
  - **Bài tập lớn cuối khóa (Final Assignment):** Simulating một buổi phỏng vấn kỹ thuật gồm hai phần: phân tích độ phức tạp Big O của 4 hàm cho trước, và lập trình giải thuật tính tổng các chữ số của một số nguyên lớn mà không được chuyển đổi sang kiểu chuỗi (String).
- **Mục tiêu học tập chính:**
  - Nắm vững kiến trúc phần cứng và kỹ thuật lập trình song song GPU để tối ưu hóa các tác vụ tính toán hình học hoặc xử lý đồ họa nặng.
  - Làm chủ cách thiết kế và giao tiếp với API để tích hợp các dịch vụ bên ngoài (như AI, Database) vào pipeline của studio.
  - Hiểu sâu về LLMs, prompt engineering và fine-tuning để tự xây dựng các trợ lý AI thông minh hỗ trợ nghệ sĩ đồ họa 3D.
  - Có cái nhìn bao quát về DevOps và Deployment để tự tin đóng gói, phân phối và quản lý hạ tầng công cụ pipeline.
  - Rèn luyện kỹ năng giải quyết thuật toán tối ưu (Big O) và chuẩn bị tốt cho các vòng phỏng vấn kỹ thuật (Technical Interviews) tại các studio lớn hoặc tập đoàn công nghệ.

---

## 2. File-by-File Analysis

### 📄 File: 01_intro.txt

**Chủ đề chính:**
- Giới thiệu tổng quan nội dung tuần học cuối cùng (Week 08).
- Định hướng công nghệ và lộ trình tự phát triển cho Technical Artist.
- Khuyến khích tư duy nghiên cứu khoa học cấp thấp (low-level) thay vì chỉ làm người dùng công cụ (black-box user).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học mở đầu tuần 8 bằng cách vạch ra lộ trình công nghệ tiếp theo cho Technical Artist sau khi khóa học kết thúc. Giảng viên điểm lại các cột mốc đã đi qua: từ thuật toán cơ bản, cấu trúc dữ liệu, OOP, SOLID đến lập trình mạng và dữ liệu lớn. Trọng tâm tuần này là tích hợp các thư viện AI tiên tiến vào Houdini, thiết kế API riêng, tìm hiểu kiến trúc máy tính nâng cao (kernels, CPU/GPU) và rèn luyện thuật toán thực hành phỏng vấn. Giảng viên đưa ra thông điệp mạnh mẽ: TA không được "black-box" (coi mọi thứ là hộp đen) hay chỉ làm người sử dụng thụ động; muốn nâng cao giá trị bản thân trong studio và tránh rủi ro sa thải, TA phải là người hiểu sâu cấu trúc phần cứng/phần mềm và tự tay xây dựng nên các công cụ đó.
- **Các khái niệm quan trọng:** Technology roadmap, low-level computer architecture, hardware-software handshake, AI API integration in Houdini, custom tool building value.
- **Dạng nội dung:** Tổng quan định hướng (Overview).

**Mức độ sâu:**
- 🟢 Nông / Chủ yếu khái niệm.

**Điểm nổi bật:**
- Truyền cảm hứng và định hình tư duy phát triển nghề nghiệp dài hạn cho TA: đi sâu vào bản chất phần cứng và thuật toán để trở thành nhân sự không thể thay thế trong studio.

**Điểm hạn chế / Thiếu sót:**
- Không có phần viết mã hay hướng dẫn kỹ thuật cụ thể do là video giới thiệu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Rất quan trọng để xác định hướng đi và thái độ học tập nghiêm túc cho TA.

---

### 📄 File: 02_gpu_kernel.txt

**Chủ đề chính:**
- Kiến trúc phần cứng GPU và phân phối tác vụ song song (Grid, Block, Thread).
- So sánh bộ nhớ chia sẻ (Shared Memory) với bộ nhớ toàn cục (Global Memory).
- Lập trình GPU Kernel tùy chỉnh bằng Python sử dụng thư viện Numba (`numba.cuda`).
- Triển khai thuật toán nhân ma trận song song trên GPU và benchmark hiệu năng.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên giới thiệu về lập trình tăng tốc phần cứng trên GPU. Trái với CPU có ít nhân nhưng cực mạnh, GPU có hàng nghìn nhân nhỏ hoạt động song song. Cấu trúc phân cấp xử lý GPU gồm: Thread (đơn vị thực thi nhỏ nhất chạy bản sao của kernel), Block (nhóm các thread có thể đồng bộ hóa và chia sẻ bộ nhớ), Grid (tập hợp tất cả các block chạy chung một kernel). Giảng viên hướng dẫn viết một GPU Kernel nhân ma trận bằng Python sử dụng Numba. Trong kernel, giảng viên khai báo mảng bộ nhớ chia sẻ `cuda.shared.array()` có kích thước cố định tại thời điểm biên dịch, sử dụng tọa độ thread/block (`cuda.threadIdx`, `cuda.blockIdx`, `cuda.grid`) để phân chia dữ liệu, đồng bộ hóa các luồng bằng `cuda.syncthreads()` để preload dữ liệu vào shared memory trước khi tính tổng tích lũy. Kết quả chạy thử nghiệm cho thấy GPU (RTX 3080) thực hiện nhân ma trận kích thước cực lớn với tốc độ vượt trội hoàn toàn so với CPU đơn luồng.
- **Các khái niệm quan trọng:** CPU vs GPU acceleration, GPU hierarchy (Thread/Block/Grid), Shared memory tiling, `@cuda.jit` decorator, `cuda.syncthreads()`, Numba & CUDA toolkit.
- **Dạng nội dung:** Lập trình tối ưu hóa phần cứng nâng cao (Hardware-level programming).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Yêu cầu hiểu sâu về toán ma trận, đồng bộ hóa luồng và quản lý bộ nhớ cache của GPU).

**Điểm nổi bật:**
- Demo thực tế việc kết nối từ xa qua SSH đến máy Linux chạy card NVIDIA để thực hiện biên dịch JIT và nhân ma trận, mô phỏng chính xác môi trường làm việc server-client của studio.

**Điểm hạn chế / Thiếu sót:**
- Không hướng dẫn chi tiết cách cài đặt driver CUDA hay cấu hình compiler trên các hệ điều hành khác nhau (như Windows), vốn là bước rất dễ gặp lỗi thiết lập.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ giá trị cho các TA muốn tối ưu hóa các node tính toán mô phỏng vật lý (dynamics solver), xử lý hạt (particles) hoặc biến đổi hình học mesh nặng trong Houdini bằng GPU.

---

### 📄 File: 03_api_design.txt

**Chủ đề chính:**
- Định nghĩa và vai trò của API (Application Programming Interface) trong giao tiếp phần mềm.
- Các loại API phổ biến: Web API (HTTP), Library API (như NumPy), OS API (Graphic UI).
- Giới thiệu các mô hình thiết kế Web API (REST, SOAP, GraphQL) và các nhà cung cấp AI API (OpenAI, Mistral, Perplexity).
- Xây dựng Web API cục bộ bằng framework FastAPI và kiểm thử bằng thư viện `requests`.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên dùng phép ẩn dụ thực tế về thực đơn nhà hàng (với khách hàng là client, bếp là backend, thực đơn/bồi bàn là API) để giải thích cơ chế Request-Response của API. Bài học tập trung vào Web API sử dụng giao thức HTTP. Giảng viên giới thiệu cách đăng ký tài khoản và quản lý API Keys (cảnh báo bảo mật giữ key riêng tư) trên các nền tảng AI lớn. Tiếp theo, học viên thực hành viết một API nhỏ bằng FastAPI trong `main.py`: khởi tạo `app = FastAPI()`, định nghĩa route trang chủ `@app.get("/")`, và route động `@app.get("/items/{item_id}")` nhận cả tham số đường dẫn và tham số truy vấn (query parameter `q`). API được chạy thông qua Uvicorn (`uvicorn main:app --reload`). Cuối cùng, giảng viên viết script client `call_test.py` sử dụng thư viện `requests.get()` để gọi và in ra kết quả JSON từ API vừa dựng.
- **Các khái niệm quan trọng:** API definition, HTTP Request-Response, API Keys security, FastAPI framework, Uvicorn server, `requests` library in Python.
- **Dạng nội dung:** Lập trình mạng & Thiết kế hệ thống (Network & System design).

**Mức độ sâu:**
- 🔴 Sâu / Kỹ thuật (Hướng dẫn đầy đủ cả phần backend API server và frontend client script).

**Điểm nổi bật:**
- Sử dụng FastAPI - một framework hiện đại bậc nhất của Python có tốc độ thực thi rất nhanh và tự động sinh tài liệu API (Swagger UI), giúp học viên dễ dàng tiếp cận lập trình web service.

**Điểm hạn chế / Thiếu sót:**
- Chưa hướng dẫn cách cấu hình bảo mật API (như Bearer Token hay OAuth2) hoặc cách deploy FastAPI server lên môi trường cloud thực tế.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Rất quan trọng để TA xây dựng các dịch vụ dùng chung trong studio (như Asset Server, License Monitor) hoặc gọi các API dịch vụ AI từ bên ngoài.

---

### 📄 File: 04_intro_to_language_models.txt

**Chủ đề chính:**
- Giới thiệu lĩnh vực NLP (Natural Language Processing) và mô hình ngôn ngữ lớn (LLMs).
- Phân tích hạn chế của kiến trúc RNNs (Recurrent Neural Networks) truyền thống.
- Kiến trúc Transformers hiện đại và cơ chế chú ý (Attention / Self-Attention).
- Phân loại Transformers: Encoder-only (BERT), Decoder-only (GPT), Encoder-Decoder (T5).
- Các tham số cấu hình mô hình: `max_tokens`, top_k, top_p, temperature và phương pháp lấy mẫu (Greedy vs Random sampling).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu lý thuyết nền tảng của LLMs. Giảng viên phân tích kiến trúc RNNs cũ xử lý văn bản tuần tự theo thời gian nên rất chậm và nhanh chóng quên ngữ cảnh đầu trang khi đọc đến cuối trang do giới hạn bộ nhớ. Sự ra đời của kiến trúc Transformers sử dụng cơ chế **Self-Attention** (Tự chú ý) đã giải quyết triệt để vấn đề này bằng cách tính toán ma trận trọng số tương quan giữa toàn bộ các từ trong câu (ví dụ: liên kết từ "he" với "dog", "ate" với "apple" trong câu "My dog ate the apple, he is happy") một cách song song. Transformers được chia làm 3 loại: Encoder-only (phù hợp phân tích sắc thái, điền từ trống), Decoder-only (phù hợp sinh văn bản như GPT), và Encoder-Decoder (phù hợp dịch thuật, tóm tắt). Giảng viên giải thích cặn kẽ các tham số điều chỉnh mô hình: `max_tokens` giới hạn độ dài câu trả lời; `top_k` và `top_p` lọc các từ có xác suất cao nhất; `temperature` điều chỉnh độ phẳng của phân phối xác suất để tăng tính sáng tạo hoặc tính chính xác của câu trả lời.
- **Các khái niệm quan trọng:** NLP, RNN memory bottleneck, Transformers, Self-Attention weights, Encoder/Decoder models, Greedy vs Random sampling, Temperature creativity.
- **Dạng nội dung:** Lý thuyết khoa học máy tính & Trí tuệ nhân tạo (AI/ML Theory).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rất trực quan các khái niệm toán học và kiến trúc mạng mà không làm học viên bị ngợp).

**Điểm nổi bật:**
- Giải thích cơ chế tự chú ý (Self-Attention) cực kỳ dễ hiểu bằng ví dụ câu nói trực quan và sơ đồ liên kết trọng số tương quan từ vựng.

**Điểm hạn chế / Thiếu sót:**
- Không đi sâu vào công thức toán học của hàm Softmax hay cơ chế Multi-Head Attention chi tiết, chỉ dừng lại ở mô tả khái niệm mức cao.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cung cấp nền tảng kiến thức bắt buộc để TA hiểu cách vận hành của các chatbot hoặc hệ thống AI tạo sinh đang bùng nổ trong ngành công nghiệp sáng tạo.

---

### 📄 File: 05_prompt_engineering_fine_tuning (1440p).txt

**Chủ đề chính:**
- Cửa sổ ngữ cảnh (Context Window) trong các mô hình ngôn ngữ.
- Kỹ thuật học trong ngữ cảnh (In-Context Learning - ICL): Zero-shot, One-shot, Few-shot.
- Khái niệm và vai trò của Prompt Engineering trong việc dẫn dắt mô hình cục bộ.
- Khái niệm Fine-tuning truyền thống vs PEFT (Parameter-Efficient Fine-Tuning) / LoRA (Low-Rank Adaptation).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học phân tích cách tối ưu hóa sự tương tác với LLMs. ICL là phương pháp hướng dẫn mô hình ngay trong Context Window mà không cần huấn luyện lại. Zero-shot không cung cấp ví dụ nào; One-shot cung cấp 1 ví dụ mẫu; Few-shot (hoặc Two-shot) cung cấp nhiều ví dụ mẫu đại diện cho các trường hợp khác nhau (ví dụ: 1 review tốt -> rating Good, 1 review xấu -> rating Bad). Điều này đặc biệt quan trọng với các mô hình local nhỏ (như Llama) vốn có ít tham số hơn các siêu mô hình chạy cloud (như GPT-4). Giảng viên hướng dẫn cách cấu trúc dữ liệu private của công ty (như dùng Pandas trích xuất tiêu đề, ID, nội dung tài liệu) để lập trình nhúng tự động vào prompt mẫu hệ thống. Cuối cùng, bài học giải thích Fine-tuning: thay vì huấn luyện lại toàn bộ hàng tỷ tham số của mô hình (rất đắt đỏ), ta sử dụng PEFT hoặc LoRA để chỉ cập nhật một nhóm nhỏ các lớp tham số chuyên biệt (ví dụ: huấn luyện thêm khả năng dạy toán học cho mô hình base), giúp tiết kiệm tài nguyên và có thể thực hiện trên một GPU cục bộ.
- **Các khái niệm quan trọng:** Context window, In-Context Learning (Zero/One/Few-shot), System prompt automation, Full Fine-tuning vs PEFT, LoRA adapters.
- **Dạng nội dung:** Kỹ thuật tương tác AI & Tối ưu hóa mô hình (Prompt Engineering & Model Fine-tuning).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rõ bản chất hoạt động của LoRA và các phương thức nạp ngữ cảnh).

**Điểm nổi bật:**
- Làm rõ sự khác biệt quan trọng giữa Prompt Engineering (chỉ thay đổi văn bản đầu vào trong context window) và Fine-tuning (thực sự thay đổi trọng số/weights của các lớp trong mô hình).

**Điểm hạn chế / Thiếu sót:**
- Không có phần thực hành huấn luyện LoRA thực tế bằng Python (như dùng Hugging Face hay PyTorch) do giới hạn thời lượng khóa học.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA hiểu cách xây dựng các trợ lý AI tùy chỉnh sử dụng dữ liệu quy trình nội bộ của studio một cách an toàn và tiết kiệm.

---

### 📄 File: 06_llms_apis.txt

**Chủ đề chính:**
- Thực hành gọi mô hình ngôn ngữ Mistral 7B cục bộ bằng framework **MLX** trên Apple Silicon.
- Giới thiệu nền tảng chạy mô hình AI thông qua API đám mây **Replicate** (`replicate.com`).
- Lập trình Python gọi mô hình Llama-2-70b-chat qua API của Replicate.
- Thiết lập System Prompt (Pre-prompt) và tinh chỉnh các tham số `temperature`, `max_length`, `repetition_penalty`.

**Nội dung chi tiết:**
- **Tóm tắt:** Học viên bắt đầu thực hành gọi API LLM. Giảng viên demo nhanh cách load Mistral-7B cục bộ bằng thư viện `mlx_lm` trên Mac, đặt giới hạn `max_tokens=50` để tăng tốc độ phản hồi. Tiếp theo, đối với các máy không có phần cứng Apple Silicon, giảng viên giới thiệu dịch vụ Replicate để chạy AI qua API đám mây. Sử dụng thư viện `replicate` của Python, giảng viên cấu hình một pre-prompt hệ thống: "You are a math teacher. Do not respond as a student". Pre-prompt này được ghép với câu hỏi của người dùng và từ khóa dẫn dắt "AI: " trong một f-string. Cuối cùng, thực hiện gọi hàm `replicate.run()` truyền vào ID mô hình Llama-2-70b, set `temperature=0.1` để tăng tính chính xác, và in ra kết quả câu trả lời toán học được stream về dòng theo dòng.
- **Các khái niệm quan trọng:** MLX framework (Apple Silicon), Replicate cloud API, System pre-prompt, Llama-2 model invocation, repetition penalty parameter.
- **Dạng nội dung:** Thực hành lập trình gọi API AI (AI API Integration coding).

**Mức độ sâu:**
- 🔴 Sâu / Kỹ thuật (Cài đặt môi trường, quản lý API tokens và xử lý luồng generator trả về từ API).

**Điểm nổi bật:**
- Minh họa rõ nét cơ chế Prompt Engineering hoạt động trong code: đóng gói pre-prompt hệ thống ngầm để định hình tính cách và bối cảnh cho AI trước khi nhận input của người dùng.

**Điểm hạn chế / Thiếu sót:**
- Việc sử dụng API Replicate có tính phí (dù có lượt thử miễn phí), học viên cần có thẻ thanh toán quốc tế để tạo API token nếu muốn thực hành lâu dài.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cung cấp đoạn code mẫu chuẩn để TA kết nối bất kỳ công cụ DCC nào với các mô hình trí tuệ nhân tạo mạnh mẽ nhất hiện nay.

---

### 📄 File: 07_houdini_replicatetools.txt

**Chủ đề chính:**
- Tạo shelf tools tương tác trong Houdini gọi mã nguồn Python ngoài.
- Dùng `hou.ui.readInput()` để tạo hộp thoại nhập prompt từ nghệ sĩ đồ họa.
- Thiết kế trợ lý AI Houdini (Llama Assistant) tự động trả lời chuyên biệt về bối cảnh Houdini (OSL, PDG, MatNet).
- Dựng công cụ AI Texture Generator sử dụng Stable Diffusion qua Replicate.
- Tiền xử lý prompt ngầm (High-res, realistic, tileable) và download ảnh tự động qua `urllib.request`.
- Giải quyết lỗi xác thực SSL trên macOS bằng cách cấu hình file Certifi `.pem`.

**Nội dung chi tiết:**
- **Tóm tắt:** Tích hợp AI trực tiếp vào quy trình làm việc của nghệ sĩ 3D trong Houdini. Giảng viên hướng dẫn tạo shelf tool, dùng `sys.path.append` trích xuất folder script ngoài và dùng `importlib.reload` để cập nhật code nóng không cần restart Houdini.
  1. Trợ lý AI Houdini: Dùng `hou.ui.readInput()` nhận câu hỏi của nghệ sĩ. Trong backend, code tự động chèn pre-prompt: "You are a Houdini AI assistant. Please respond to everything in SideFX Houdini context". Nhờ đó, khi hỏi "làm sao để tạo material network", AI trả lời chính xác các bước trong Houdini thay vì Maya hay Unreal.
  2. Dựng AI Texture Generator: Nhận prompt như "brick wall", code tự động cộng thêm từ khóa chất lượng ("high resolution, realistic, tileable if possible") rồi gửi lên Replicate chạy Stable Diffusion. URL ảnh trả về được tải về thư mục cục bộ qua `urllib.request.urlretrieve()` và gán trực tiếp vào tham số `map` của node shader được chọn: `tex_node.parm("map").set(local_file_path)`. Giảng viên cũng lưu ý cách sửa lỗi SSL trên Mac bằng cách chỉ định biến môi trường `SSL_CERT_FILE` trỏ đến file `.pem` của thư viện `certifi`.
- **Các khái niệm quan trọng:** Houdini Shelf tool customization, `hou.ui.readInput()`, system prompt encapsulation, urllib texture download, automatic parameter assignment (`parm.set()`), SSL certifi environment fix.
- **Dạng nội dung:** Lập trình công cụ DCC & Tích hợp AI thực hành (Custom Houdini & AI integration).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Can thiệp trực tiếp vào UI Houdini, hệ thống tệp tin hệ điều hành, biến môi trường SSL và quản lý tham số node).

**Điểm nổi bật:**
- Một ví dụ thực tế hoàn hảo về việc tạo ra giá trị to lớn cho studio: tích hợp AI tạo texture ngay trong viewport Houdini chỉ với một nút bấm trên shelf, giúp nghệ sĩ tiết kiệm hàng giờ tìm kiếm texture trên mạng.

**Điểm hạn chế / Thiếu sót:**
- Code tải file ảnh sử dụng cơ chế đồng bộ (blocking code), nghĩa là khi ảnh đang được download từ server Replicate, giao diện Houdini sẽ bị đóng băng tạm thời cho đến khi tải xong.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là kỹ năng cốt lõi giúp TA xây dựng các công cụ thế hệ mới thông minh và tự động hóa cao.

---

### 📄 File: 08_deployment_concepts.txt

**Chủ đề chính:**
- Tổng quan các phương pháp đóng gói và quản lý môi trường ảo (virtual environments, requirements, `setup.py`).
- Khái niệm Containerization (Docker) và Orchestration (Kubernetes).
- Cloud hosting platform (PaaS) như Heroku, Vercel, Next.js.
- Cơ chế ánh xạ cơ sở dữ liệu hướng đối tượng ORM (Prisma & PostgreSQL).
- Triết lý WebAssembly (WASM - "HTML is the new .exe") và PythonAnywhere.
- Khái niệm Serverless computing và phân phối thư viện qua PyPI.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học cung cấp bức tranh toàn cảnh về DevOps và phân phối phần mềm. Bắt đầu từ đóng gói Python đơn giản bằng `requirements.txt` (`pip install -r`) và `setup.py` để phân phối package lên PyPI. Tiếp theo là Docker - công cụ đóng gói toàn bộ hệ điều hành, thư viện và mã nguồn vào một "Container" độc lập để chạy mọi nơi không lo xung đột cấu trúc máy. Kubernetes đóng vai trò nhạc trưởng điều phối hàng trăm container Docker đó. Giảng viên giới thiệu mô hình PaaS (Heroku, Vercel) chạy web server, Next.js và giới thiệu ORM (như Prisma) làm lớp trung gian giúp lập trình viên thao tác với database PostgreSQL bằng cú pháp hướng đối tượng thân thiện thay vì viết các câu lệnh SQL thô. WebAssembly (WASM) được nhấn mạnh là công nghệ tương lai cho phép biên dịch mã C++, Rust hay Python để chạy trực tiếp trên trình duyệt client với hiệu năng cực cao. Cuối cùng, giảng viên phân tích Serverless computing (tự động co giãn tài nguyên theo nhu cầu thực tế, dùng bao nhiêu trả bấy nhiêu nhưng dễ bị vượt ngân sách nếu code không tối ưu) và PythonAnywhere để chạy các task Python ngầm theo lịch trình.
- **Các khái niệm quan trọng:** requirements.txt, Docker containers, Kubernetes orchestrator, PaaS, ORM (Prisma/PostgreSQL), WebAssembly (WASM), Serverless cloud billing, PyPI distribution.
- **Dạng nội dung:** Lý thuyết DevOps & Triển khai hệ thống (DevOps & Deployment architecture).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rõ bản chất, ưu nhược điểm và ngữ cảnh áp dụng của từng công nghệ triển khai).

**Điểm nổi bật:**
- Giải thích cực kỳ trực quan triết lý "HTML là file .exe mới" thông qua WASM, mở ra hướng phát triển các công cụ đồ họa chạy trực tiếp trên trình duyệt mà không cần cài đặt.

**Điểm hạn chế / Thiếu sót:**
- Do số lượng công nghệ quá lớn, bài học chỉ dừng lại ở mức giới thiệu khái niệm và thuật ngữ, không đi sâu vào thực hành viết Dockerfile hay deploy thực tế.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA hiểu cách đóng gói các công cụ pipeline phức tạp để phân phối cho hàng trăm artist trong studio sử dụng các hệ điều hành khác nhau (Windows/Linux/macOS) một cách đồng nhất.

---

### 📄 File: 09_algorithms_in_practice.txt

**Chủ đề chính:**
- Tầm quan trọng của giải thuật tối ưu (Big O) trong các buổi phỏng vấn kỹ thuật (Technical Interviews).
- Giải toán LeetCode 1: **Two Sum** - tối ưu bằng Hash Table (Python dictionary) từ $O(N^2)$ xuống $O(N)$ thời gian và $O(N)$ không gian.
- Giải toán LeetCode 2: **Three Sum** - tối ưu bằng kỹ thuật hai con trỏ (Two Pointers) trên mảng đã sắp xếp thành $O(N^2)$ thời gian.
- Giải toán LeetCode 3: **Valid Palindrome** - tối ưu bằng hai con trỏ chạy từ hai đầu chuỗi đạt $O(N)$ thời gian và $O(1)$ không gian.
- Giải toán LeetCode 4: **Longest Common Prefix** - tối ưu bằng so sánh chuỗi ngắn nhất với tập hợp ký tự duy nhất (Set intersection).

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên hướng dẫn tư duy giải quyết thuật toán để vượt qua các vòng phỏng vấn kỹ thuật. Quy tắc vàng: Đọc kỹ đề, hỏi rõ các trường hợp đặc biệt (edge cases) với người phỏng vấn, trình bày giải pháp thô (brute force) trước rồi mới đưa ra giải pháp tối ưu.
  1. Two Sum: Tìm hai số có tổng bằng target. Brute force dùng 2 vòng lặp lồng nhau $O(N^2)$. Giải pháp tối ưu dùng dictionary lưu giá trị đã duyệt. Khi duyệt số hiện tại, tính `complement = target - num`, nếu `complement` có trong dictionary thì trả về ngay chỉ số của chúng ($O(N)$ thời gian).
  2. Three Sum: Tìm bộ ba số có tổng bằng target. Tối ưu bằng cách sắp xếp mảng ($O(N \log N)$), cố định một số và dùng kỹ thuật 2 con trỏ (left chạy từ đầu, right chạy từ cuối mảng) dịch chuyển dựa trên tổng hiện tại so với target ($O(N^2)$ thời gian).
  3. Valid Palindrome: Kiểm tra chuỗi đối xứng. Thay vì đảo ngược chuỗi tốn bộ nhớ $O(N)$, dùng 2 con trỏ (left=0, right=len-1) so sánh các ký tự tương ứng và dịch chuyển dần vào giữa ($O(1)$ bộ nhớ).
  4. Longest Common Prefix: Tìm tiền tố chung dài nhất. Cách làm là tìm từ ngắn nhất trong danh sách, tạo một set các ký tự của từ đó, duyệt qua các từ khác và dùng phương thức loại bỏ các ký tự không xuất hiện trong các từ đó ra khỏi set, cuối cùng join lại thành chuỗi.
- **Các khái niệm quan trọng:** LeetCode interview preparation, Two Sum hash-map solution, Three Sum sorted array two-pointers, Valid Palindrome constant space check, Longest Common Prefix set intersection.
- **Dạng nội dung:** Lập trình giải thuật thực hành (Algorithm coding & Optimization).

**Mức độ sâu:**
- 🔴 Sâu / Rất kỹ thuật (Phân tích chi tiết từng dòng code giải thuật và chứng minh toán học cho độ phức tạp Big O).

**Điểm nổi bật:**
- Nhấn mạnh kỹ năng giao tiếp trong phỏng vấn kỹ thuật: giải thích tư duy logic rõ ràng trên bảng trắng (whiteboard) quan trọng hơn việc viết code hoàn hảo không lỗi cú pháp.

**Điểm hạn chế / Thiếu sót:**
- Thuật toán Longest Common Prefix sử dụng Set để loại bỏ ký tự không trùng lặp có thể bị sai thứ tự ký tự nếu không được xử lý cẩn thận, vì Set trong Python mặc định không bảo toàn thứ tự chèn.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Rèn luyện tư duy tối ưu hóa thuật toán cực tốt cho TA khi phải xử lý các vòng lặp duyệt qua hàng chục triệu polygon hoặc point trong Houdini geometry.

---

### 📄 File: 10_interview_process.txt

**Chủ đề chính:**
- Hướng dẫn xây dựng portfolio phù hợp cho từng định hướng nghề nghiệp (TA Animation, Pipeline TD, Fullstack, AI/ML).
- Tầm quan trọng của việc kết nối mạng lưới (networking) trên LinkedIn và các sự kiện thực tế.
- Chi tiết các bước trong quy trình tuyển dụng tại các tập đoàn lớn (Screning call, Technical interview, On-site full-day interview).
- Kỹ năng phỏng vấn hành vi (Behavioral interview) và cách đối mặt với sự từ chối (rejection).

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên chia sẻ kinh nghiệm tuyển dụng trong ngành công nghệ. Đầu tiên, TA cần xây dựng portfolio tập trung vào thế mạnh cụ thể: ví dụ TA Animation cần show các tool tự động hóa rig nhân vật; Pipeline TD cần show các tool giao tiếp server, API và phân tích hiệu năng. Quy trình tuyển dụng thường gồm các bước:
  1. Phone screen: Recruiter gọi điện kiểm tra thông tin cơ bản.
  2. Second screening: Trò chuyện sâu hơn với quản lý chuyên môn về vai trò cụ thể.
  3. Team call: Trò chuyện với các thành viên trong team để đánh giá mức độ hòa nhập.
  4. Technical interview: Phỏng vấn giải thuật trực tuyến (live coding).
  5. On-site interview: Phỏng vấn trực tiếp cả ngày tại văn phòng công ty (4-5 cuộc phỏng vấn liên tục bao gồm code bảng trắng - whiteboard coding, phỏng vấn hành vi - behavioral interview về cách giải quyết xung đột, áp lực công việc). Giảng viên khuyên học viên luôn giữ vững sự tự tin vì tiêu chuẩn tuyển dụng kỹ sư lương cao là rất khắt khe, việc bị từ chối là bình thường và là cơ hội để cải thiện.
- **Các khái niệm quan trọng:** Specialized portfolio, recruiter screening, live coding interview, whiteboard coding, behavioral interview questions, handling rejection.
- **Dạng nội dung:** Định hướng nghề nghiệp & Kỹ năng mềm (Career guidance & Interview skills).

**Mức độ sâu:**
- 🟡 Trung bình (Cung cấp các lời khuyên thực tế từ góc nhìn của người phỏng vấn lâu năm).

**Điểm nổi bật:**
- Phân tích chi tiết quy trình phỏng vấn On-site khắc nghiệt tại các tập đoàn lớn (Big Tech), giúp học viên chuẩn bị trước tâm lý và chiến thuật ứng phó hiệu quả.

**Điểm hạn chế / Thiếu sót:**
- Không đề cập đến các câu hỏi phỏng vấn hành vi cụ thể (ví dụ theo phương pháp STAR: Situation, Task, Action, Result) thường gặp trong thực tế.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ cần thiết cho các TA chuẩn bị xin việc hoặc muốn thăng tiến lên các vị trí cao hơn trong các studio quốc tế.

---

### 📄 File: 11_final.txt

**Chủ đề chính:**
- Chúc mừng học viên hoàn thành khóa học "Rebelway - Python For Production".
- Giới thiệu kho lưu trữ code mẫu chung của khóa học (Houdini Utils Git repo).
- Tầm quan trọng của lập trình trong thế giới hiện đại được vận hành bằng mã nguồn và dữ liệu.
- Gợi ý định hướng cho các khóa học công nghệ tiếp theo.

**Nội dung chi tiết:**
- **Tóm tắt:** Video kết thúc khóa học gửi lời chúc mừng đến các học viên đã kiên trì đi đến chặng đường cuối cùng. Giảng viên thông báo học viên sẽ có quyền truy cập vào kho lưu trữ Git chung có tên là "Houdini Utils", chứa toàn bộ code mẫu của các tuần học được chia theo từng branch cụ thể. Giảng viên tái khẳng định chúng ta đang sống trong một thực tế được vận hành hoàn toàn bằng mã nguồn và dữ liệu (từ nút bấm thang máy, đèn giao thông, đến hệ thống siêu thị hay smartphone). Nếu không biết lập trình, chúng ta sẽ bị tụt hậu và đứng ngoài sự phát triển này. Cuối cùng, giảng viên đưa ra gợi ý ẩn ý về một dự án/khóa học công nghệ mới đầy hứa hẹn sắp ra mắt.
- **Các khái niệm quan trọng:** Course completion, Houdini Utils Git branches, software-driven world, coding literacy, technology future.
- **Dạng nội dung:** Tổng kết khóa học (Course Wrap-up).

**Mức độ sâu:**
- 🟢 Nông / Tổng kết truyền cảm hứng.

**Điểm nổi bật:**
- Nhấn mạnh tính ứng dụng thực tế của lập trình trong cuộc sống hàng ngày, củng cố thêm niềm tin và động lực tiếp tục học tập của học viên.

**Điểm hạn chế / Thiếu sót:**
- Không có nội dung kỹ thuật mới vì là bài phát biểu bế mạc.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Tạo động lực tinh thần to lớn cho TA tiếp tục hành trình nghiên cứu công nghệ.

---

### 📄 File: 12-assignment.txt

**Chủ đề chính:**
- Mô tả chi tiết yêu cầu của bài tập lớn cuối khóa (Final Assignment).
- Phần 1: Phân tích độ phức tạp Big O (Time & Space) của 4 hàm Python cho trước.
- Phần 2: Lập trình thuật toán tính tổng các chữ số của một số nguyên không sử dụng ép kiểu chuỗi (String conversion).
- Khuyên học viên tự lực cánh sinh, không gian lận bằng cách chép code từ AI.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài tập lớn cuối khóa được thiết kế mô phỏng một buổi phỏng vấn kỹ thuật thực tế để học viên tự đánh giá năng lực của mình. Bài tập gồm 2 phần:
  1. Phân tích độ phức tạp: Học viên phải đọc mã nguồn của 4 hàm Python (A, B, C, D) có sẵn trong file bài tập tải về từ Git repo, sau đó phân tích và ghi rõ độ phức tạp thời gian (Time Complexity) và không gian (Space Complexity) dưới dạng ký hiệu Big O.
  2. Lập trình giải thuật: Viết chương trình nhận vào một số nguyên dương (ví dụ: 1234) và tính tổng các chữ số của nó (1 + 2 + 3 + 4 = 10). Ràng buộc bắt buộc: **Không được chuyển đổi số nguyên sang kiểu string** (ví dụ cấm dùng `str(num)` rồi loop). Học viên phải sử dụng các phép toán số học như chia lấy dư `% 10` để lấy chữ số cuối cùng và chia lấy phần nguyên `// 10` để dịch chuyển số. Giảng viên nhấn mạnh học viên cần tự làm một cách trung thực để rèn luyện tư duy thực chất thay vì dùng ChatGPT làm hộ.
- **Các khái niệm quan trọng:** Final assignment guidelines, Big O analysis task, digit sum mathematical algorithm (modulo & floor division), academic integrity warning.
- **Dạng nội dung:** Hướng dẫn bài tập lớn cuối khóa (Assignment Brief).

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rõ ràng các đầu việc và các ràng buộc kỹ thuật của bài tập).

**Điểm nổi bật:**
- Ràng buộc "không chuyển đổi sang string" buộc học viên phải vận dụng tư duy toán học và xử lý số nhị phân/thập phân cơ bản, đây là một câu hỏi phỏng vấn tư duy rất phổ biến.

**Điểm hạn chế / Thiếu sót:**
- Không hiển thị trực tiếp code của 4 hàm A, B, C, D trong video/transcript mà yêu cầu học viên phải tự tải về từ repo để xem.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp học viên tổng hợp toàn bộ kiến thức về thuật toán, Big O và tư duy lập trình tối ưu đã học trong suốt 8 tuần để giải quyết một bài kiểm tra thực chất.

---

## 3. Weekly Summary

### Tổng kết nội dung học tập
Week 08 đã kết thúc khóa học bằng một chuỗi kiến thức tích hợp đỉnh cao từ lập trình phần cứng cấp thấp (GPU Kernel với Numba), thiết kế mạng (FastAPI), tương tác mô hình ngôn ngữ lớn (Transformers, Prompt Engineering, Fine-tuning), viết công cụ AI tạo texture trực quan trong Houdini viewport, cho đến các khái niệm triển khai DevOps toàn diện và giải thuật thực hành phỏng vấn LeetCode (Two/Three Sum, Palindrome, Prefix).

### Bài học cốt lõi & Tư duy Technical Artist
1. **Làm chủ phần cứng (CPU vs GPU):** TA không chỉ dừng lại ở việc viết code Python chạy tuần tự trên CPU. Nắm vững GPU programming (Thread/Block/Grid) và tận dụng Numba để viết GPU kernels tùy chỉnh giúp giải quyết các bài toán tính toán lưới 3D nặng đô với tốc độ xử lý vượt trội.
2. **Tư duy thiết kế API mở:** Hiểu cấu trúc API (Request-Response, Endpoints, FastAPI) giúp TA tự dựng các dịch vụ backend phục vụ quản lý asset, hoặc kết nối linh hoạt công cụ DCC với các dịch vụ đám mây thông minh.
3. **Prompt Engineering & Local LLMs:** In-Context Learning (Few-shot) là chìa khóa để triển khai các mô hình local nhỏ (Llama) hoạt động chính xác trong bối cảnh sản xuất. Việc ẩn giấu pre-prompt hệ thống và các từ khóa chất lượng cao một cách tự động giúp nâng cao trải nghiệm người dùng cuối.
4. **Tích hợp AI DCC thực tế:** Việc kết hợp gọi API Stable Diffusion từ code Python của Houdini, tải ảnh tự động và gán trực tiếp vào shader parameter là minh chứng rõ nét cho vai trò của TA: biến công nghệ AI thô thành các công cụ sản xuất texture/mesh vô cùng tiện lợi cho nghệ sĩ.
5. **Đóng gói và phân phối (DevOps):** Hiểu rõ các công cụ như requirements, Docker containers, Kubernetes, WebAssembly giúp TA tự tin đóng gói công cụ pipeline chạy ổn định trên mọi máy trạm của artist mà không gặp lỗi xung đột thư viện.
6. **Vượt qua phỏng vấn thuật toán:** Việc rèn luyện giải quyết các bài toán LeetCode bằng các cấu trúc dữ liệu tối ưu (Hash table thay cho nested loops, Two pointers thay cho sao chép mảng) và khả năng trình bày tư duy logic trên bảng trắng là chìa khóa vàng để TA chinh phục các nhà tuyển dụng tại các studio hàng đầu thế giới.
