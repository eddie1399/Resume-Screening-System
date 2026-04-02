from docling.document_converter import DocumentConverter
# # 示例用法
# pdf_path = "D:\\Resume_Screening_System\\李泽沁简历.pdf"
# markdown_path = "D:\\Resume_Screening_System\\李泽沁简历.md"
# convert_pdf_to_markdown(pdf_path, markdown_path)

## 把这个操作写成一个方法，输入就是pdf文件，输出就是markdown文件
def convert_pdf_to_markdown(pdf_path, markdown_path):
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(result.document.export_to_markdown())

