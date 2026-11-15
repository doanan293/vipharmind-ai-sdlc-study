# XeLaTeX để dùng phông hệ thống có đủ dấu tiếng Việt.
$pdf_mode = 5;
$bibtex_use = 2;
$xelatex = 'xelatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
@default_files = ('de-cuong.tex');
# Trích dẫn hoặc tham chiếu chưa định nghĩa là lỗi.
$warnings_as_errors = 1;
