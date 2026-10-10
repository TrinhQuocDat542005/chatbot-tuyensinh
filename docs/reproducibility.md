# Docker, CI và model có thể truy vết

## Chạy từ clone sạch

Dùng Docker Engine Linux x86_64, Git và Python 3.10+ để chạy script quản lý. Python trên host chỉ chạy thư viện chuẩn; Rasa/TensorFlow được cài trong container Python 3.10. Lần build sạch cần Internet để tải base image và package.

```bash
git clone https://github.com/TrinhQuocDat542005/chatbot-tuyensinh.git
cd chatbot-tuyensinh
python scripts/manage.py train
python scripts/manage.py up
python scripts/manage.py check
```

Mở <http://localhost:8686>. `train` build Rasa, SDK và web, truyền Git SHA cùng trạng thái working tree vào container, force train rồi ghi ba file:

- `models/admissions-week4.tar.gz`: tên ổn định để tương thích các script; ngày/commit thực nằm trong manifest.
- `models/admissions-week4.tar.gz.manifest.json`: commit, working tree có thay đổi hay không, thời gian UTC, lệnh train, SHA-256 từng input, package cài thực tế và hash/size model.
- `models/admissions-week4.tar.gz.sha256`: checksum dạng tương thích `sha256sum`.

`up` kiểm tra checksum và fingerprint input trước khi mở service. Rasa cũng kiểm tra lại trong container. Sửa domain, config, NLU, custom component hoặc dữ liệu action thì phải train lại. Thay đổi README không buộc train lại. Hash bảo vệ tính toàn vẹn, không thay thế chữ ký/chứng minh nguồn tin cậy của file tải về.

`python scripts/manage.py down` dừng service. `--skip-build` chỉ dùng khi đã build image từ chính checkout đang chạy, ví dụ trong CI; không dùng để bỏ qua build sau khi sửa source.

## Windows, WSL và Linux

Windows PowerShell: dùng `python` nếu Python đã có trong PATH hoặc thay bằng `py -3.10`. Mở Docker Desktop và chọn Linux containers. Các đường dẫn trong lệnh đều tương đối, không cần kích hoạt venv Rasa trên Windows. Nếu DLL scikit-learn bị Windows Application Control chặn, quy trình Docker tránh chạy DLL đó trên host.

WSL/Linux: cài Docker Engine hoặc bật WSL integration trong Docker Desktop. Clone và chạy trong cùng filesystem/môi trường; dùng `python3` thay cho `python` nếu đó là tên interpreter. Script quản lý sử dụng interpreter đang chạy để kiểm tra model.

Không cần Node để chạy demo. Kiểm tra trình duyệt tùy chọn cần Node 20+:

```bash
npm ci
npx playwright install --with-deps chromium
npm run test:web
```

Trên Windows có thể bỏ `--with-deps`; dùng `CHROME_EXECUTABLE` khi muốn dùng Chrome có sẵn. Quay video cần thêm `npx playwright install ffmpeg`.

## Image và dependency

| Thành phần | Image / dependency |
| --- | --- |
| Rasa train/run/check | `Dockerfile`, Python 3.10 Debian Bookworm, `requirements-lock.linux.txt` |
| Action server | `Dockerfile.actions` target `runtime`, `requirements-lock.actions.txt`; không có Rasa/TensorFlow |
| CI nhẹ Linux | `requirements-check.linux.txt` gồm SDK lock + test/lint; target `checks` cho kiểm tra local |
| Web gateway | `web/Dockerfile`, chỉ Python standard library |

`requirements.txt` và `requirements-actions.txt` mô tả các dependency trực tiếp; hai lock Linux khóa cả dependency bắc cầu. `requirements-lock.windows.txt` chỉ là snapshot Windows, không cài trong Linux. Base image vẫn là tag OS/Python; đây là tái lập môi trường phần mềm, chưa phải image bit-for-bit. Lock không có hash wheel; cập nhật dependency cần build sạch, `pip check` và regression đầy đủ. Dòng Rasa 3.6/TensorFlow 2.12 cần được đánh giá nâng cấp riêng trước khi public.

Để kiểm tra nhanh bằng image SDK:

```bash
docker build -f Dockerfile.actions --target checks -t chatbot-tuyensinh-checks:local .
docker run --rm chatbot-tuyensinh-checks:local python -m pytest -q
```

## Biến môi trường và log

Copy `.env.example` thành `.env` nếu cần đổi cổng host `PORT`/`ACTION_PORT`. Endpoint trong network Docker luôn là `rasa:5005` và `actions:5055`; `.env` không đổi các cổng nội bộ này. `RASA_URL` dành cho gateway chạy native, không ghi đè endpoint Compose. Web mặc định 8686. `MODEL_PATH` là tùy chọn của script native `start.sh`; quy trình Compose dùng tên model chuẩn ở trên.

SDK, Rasa và gateway gửi thông tin vận hành ra stdout/stderr. Xem `docker compose logs --tail 100` hoặc `docker compose logs -f rasa actions web`. Không bật debug hoặc ghi nguyên hội thoại khi vận hành với người dùng thật. CI chỉ sử dụng câu kiểm thử tự soạn; `results/services.log`, JUnit và báo cáo được tải lên artifact. Log CI không phải chính sách log cho demo công khai.

Healthcheck kiểm tra HTTP từng service; `depends_on: service_healthy` chờ SDK trước Rasa, Rasa trước web. Cổng host bind localhost; cấu hình này phục vụ local. `docker compose config --quiet` kiểm tra cấu hình sau nội suy `.env`.

## Hai workflow GitHub Actions

**CI** chạy mỗi PR/push main/manual: cài dependency vào môi trường mới, `pip check`, Ruff correctness (`E9/F63/F7/F82`), actionlint, parse YAML/JSON chống duplicate key, schema/reference validation, pytest và browser mock. Đây chưa phải kiểm tra style/format toàn repository. Test chứa dữ liệu lỗi có chủ đích để chứng minh gate từ chối lỗi, không sửa dataset production để thử CI.

**Model regression** chạy khi input/runtime/test thay đổi, thứ Hai 09:00 giờ Việt Nam và manual: build sạch từ lock, validation Rasa, train mới, verify provenance, Python/Core với `--fail-on-prediction-errors`, NLU authored regression, SDK/REST, 22 hội thoại có intent tường minh, 4 hội thoại bằng ngôn ngữ tự nhiên và 13 nhóm UI thật. Gate NLU yêu cầu ít nhất 150 câu/30 câu khó hoặc OOD, macro-F1 intent ≥0,90 và entity exact-span F1 ≥0,85. Tập test đã review; đây là gate hồi quy, chưa đo chất lượng người dùng mới.

Workflow có quyền `contents: read`, không deploy/publish release và không dùng secret; checkout không giữ credential. GitHub Actions được pin SHA; actionlint image được pin digest. Cache chỉ tải lại package pip/npm, vẫn cài vào môi trường mới và kiểm tra dependency. Không cache venv/model hoặc dùng cache để bỏ qua train. Luồng model build sạch mỗi lần; không dựa vào pip cache của luồng nhẹ.

## Dùng artifact model

Trong tab Actions, chọn lần **Model regression** thành công của commit mong muốn. Tải `model-<SHA>` và `evaluation-<SHA>`. Model artifact lưu 30 ngày, check report 14 ngày. Giải nén model bundle vào `models/`, checkout đúng commit rồi build image:

```bash
git checkout <SHA>
docker compose build train actions web
python scripts/model_artifact.py verify
python scripts/manage.py up
```

`verify` phải pass trước khi dùng. Không dùng tám model legacy tháng 05/2025 cho domain hiện tại. Artifact là đầu ra CI có hạn lưu. Bản portfolio v1.0.0 phân phối bundle chuẩn lâu dài qua [GitHub Release và hướng dẫn](release.md). Không tự rewrite lịch sử Git/LFS.

## Tài liệu đối chiếu

- [GitHub Actions: Python CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).
- [GitHub: workflow artifacts và cache](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts).
- [Rasa CLI: validation/train/test](https://legacy-docs-oss.rasa.com/docs/rasa/command-line-interface/).
- [actionlint: kiểm tra workflow](https://github.com/rhysd/actionlint/blob/main/docs/usage.md).
