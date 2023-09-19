# coding=utf-8
import PyPDF2
import pikepdf      # 切割PDF模块


class Cut:
    def __init__(self):
        pass

    def split_pdf(self, input_pdf, output_pdf, start_page, end_page):
        """
        切割PDF
        :param input_pdf: 完整PDF
        :param output_pdf: 切割后的PDF文件绝对路径
        :param start_page: 开始页
        :param end_page: 结束页
        :return: 返回文件绝对路径
        """
        with pikepdf.open(input_pdf) as pdf:
            if start_page < 1 or end_page > len(pdf.pages):
                raise ValueError(f"Invalid page range. The input PDF has {len(pdf.pages)} pages.")

            output = pikepdf.Pdf.new()
            for i in range(start_page - 1, end_page):
                output.pages.append(pdf.pages[i])

            output.save(output_pdf)
        return output_pdf


import fitz         # pip3 install -i https://mirrors.aliyun.com/pypi/simple PyMuPDF
# 将PDF的每一页保存为PNG
class PdfToPng:
    def __init__(self):
        pass

    def pdf_to_png(self, pdf_path, output_path, dpi=300):
        """
        将PDF的每一页保存为PNG
        :param pdf_path: 需要转换PNG的PDF
        :param output_path: PNG保存的绝对路径
        :param dpi:
        :return: 返回字典，{页数:绝对路径}
        """
        # 打开PDF文件
        pdf_document = fitz.open(pdf_path)

        result = {}
        for page_number in range(pdf_document.page_count):
            # 获取指定页
            page = pdf_document.load_page(page_number)

            # 设置图像质量和缩放比例
            zoom = dpi / 72  # 72 DPI是PDF的默认分辨率
            matrix = fitz.Matrix(zoom, zoom)

            # 将页面呈现为图像
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            # 构建输出文件名
            output_file = fr"{output_path}\_page{page_number + 1}.png"

            # 将图像保存为PNG文件
            pixmap.save(output_file)

            # 将结果添加到字典中
            result[page_number + 1] = output_file

        return result



# 百度云识别图片模块  —— ——  目前未使用
import sys
import ssl
import json
import base64
# 保证兼容python2以及python3
IS_PY3 = sys.version_info.major == 3
if IS_PY3:
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import URLError
    from urllib.parse import urlencode
    from urllib.parse import quote_plus
else:
    import urllib2
    from urllib import quote_plus
    from urllib import urlencode
class BaiDu_OCR:
    def __init__(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        pass

    def fetch_token(self, api_key, secret_key, token_url):
        params = {
            'grant_type': 'client_credentials',
            'client_id': api_key,
            'client_secret': secret_key
        }
        post_data = urlencode(params)
        if IS_PY3:
            post_data = post_data.encode('utf-8')
        req = Request(token_url, post_data)
        try:
            f = urlopen(req, timeout=5)
            result_str = f.read()
        except URLError as err:
            print(err)
        if IS_PY3:
            result_str = result_str.decode()

        result = json.loads(result_str)

        if 'access_token' in result.keys() and 'scope' in result.keys():
            if 'brain_all_scope' not in result['scope'].split(' '):
                print('please ensure has check the ability')
                exit()
            return result['access_token']
        else:
            print('please overwrite the correct API_KEY and SECRET_KEY')
            exit()


    def read_file(self, image_path):
        f = None
        try:
            f = open(image_path, 'rb')
            return f.read()
        except:
            print('read image file fail')
            return None
        finally:
            if f:
                f.close()

    def request(self, url, data):
        req = Request(url, data.encode('utf-8'))
        has_error = False
        try:
            f = urlopen(req)
            result_str = f.read()
            if (IS_PY3):
                result_str = result_str.decode()
            return result_str
        except URLError as err:
            print(err)

    def group_words_by_line(self, words_result, threshold=50):
        sorted_words = sorted(words_result, key=lambda x: x['location']['top'])
        lines = []
        current_line = []
        prev_top = sorted_words[0]['location']['top']

        for word in sorted_words:
            current_top = word['location']['top']

            if abs(current_top - prev_top) <= threshold:
                current_line.append(word)
            else:
                current_line = sorted(current_line, key=lambda x: x['location']['left'])
                lines.append(current_line)
                current_line = [word]

            prev_top = current_top

        current_line = sorted(current_line, key=lambda x: x['location']['left'])
        lines.append(current_line)

        return lines

    def get_bounding_box(self, line):
        top = min(word['location']['top'] for word in line)
        left = min(word['location']['left'] for word in line)
        bottom = max(word['location']['top'] + word['location']['height'] for word in line)
        right = max(word['location']['left'] + word['location']['width'] for word in line)

        return {
            'top': top,
            'left': left,
            'width': right - left,
            'height': bottom - top
        }

    def get_result_by_line(self, result_json):
        words_result = result_json['words_result']
        lines = self.group_words_by_line(words_result)

        result_by_line = {}

        for line_number, line in enumerate(lines, start=1):
            line_content = " ".join([word['words'] for word in line])

            line_location = self.get_bounding_box(line)

            result_by_line[line_number] = {
                'content': line_content,
                'location': line_location
            }

        return result_by_line

    def extract_paragraphs(self, result_json):
        """网络图片位置按行读取"""
        if "words_result" not in result_json:
            return {}

        words_result = result_json["words_result"]
        words_result.sort(key=lambda x: (x['location']['top'], x['location']['left']))

        paragraphs = {}
        current_paragraph = []
        previous_y = None
        y_tolerance = 50
        paragraph_index = 1

        for word_info in words_result:
            location = word_info["location"]
            x, y = location["left"], location["top"]

            if previous_y is not None and abs(y - previous_y) > y_tolerance:
                current_paragraph.sort(key=lambda w: w['location']['left'])
                paragraphs[paragraph_index] = " ".join([w["words"] for w in current_paragraph])
                current_paragraph = []
                paragraph_index += 1

            current_paragraph.append(word_info)
            previous_y = y

        if current_paragraph:
            current_paragraph.sort(key=lambda w: w['location']['left'])
            paragraphs[paragraph_index] = " ".join([w["words"] for w in current_paragraph])

        return paragraphs



import pdfplumber
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage
# from pdfminer.layout import LAParams, LTTextBoxHorizontal
import fitz
# python内置方法读取pdf
class Read_Pdf:
    def extract_text_from_pdf(self, pdf_path):
        """
            直接读取PDF整页
            :param pdf_path:
            :return:
            """
        # 打开PDF文件
        pdf_document = fitz.open(pdf_path)
        # 存储提取到的文本
        # extracted_text = ""
        # 遍历PDF中的每一页
        return_dict = {}
        for page_num in range(pdf_document.page_count):
            # 获取当前页
            page = pdf_document.load_page(page_num)
            # 提取当前页的文本
            page_text = page.get_text("text")
            # 将提取到的文本添加到结果字符串中
            try:
                return_dict[int(page_num) + 1] = page_text
            except Exception as error:
                print(error)
            # extracted_text += page_text
        return return_dict

    def extract_textline_from_pdf(self, pdf_path):
        """按行读取，不分页"""
        text_dict = {}
        line_count = 1
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().split('\n')
                for line in lines:
                    text_dict[line_count] = line
                    line_count += 1
        return text_dict

    def chinesedir_extract_text_from_pdf(self, pdf_path):
        """
        直接读取，一串STR，无换行符,不规范
        :param pdf_path:
        :return:
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text()   #.replace("\n", "")
        return text



import os
import pikepdf
from PyPDF4 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from pdfrw import PdfReader, PdfWriter, PageMerge
from PyPDF2 import PdfReader, PdfWriter
class PdfProcessor:
    def __init__(self):
        pass

    def split_pdf(self, input_pdf, output_pdf, start_page, end_page):
        with pikepdf.open(input_pdf) as pdf:
            if start_page < 1 or end_page > len(pdf.pages):
                raise ValueError(f"Invalid page range. The input PDF has {len(pdf.pages)} pages.")
            output = pikepdf.Pdf.new()
            for i in range(start_page - 1, end_page):
                output.pages.append(pdf.pages[i])
            output.save(output_pdf)

    def add_watermark(self, input_pdf, watermark_pdf, output_pdf):
        """
        给PDF添加水印，水印格式为PDF
        :param input_pdf:
        :param watermark_pdf:
        :param output_pdf:
        :return:
        """
        try:
            # 读取输入的PDF文档和水印PDF
            input_reader = PdfReader(input_pdf)
            watermark_reader = PdfReader(watermark_pdf)

            # 创建一个新的PDF写入器
            pdf_writer = PdfWriter()

            # 遍历输入文档的每一页
            for i, page in enumerate(input_reader.pages):
                # 获取当前页和水印页
                input_page = input_reader.pages[i]
                watermark_page = watermark_reader.pages[0]  # 假设水印只有一页

                # 将水印页合并到当前页
                input_page.merge_page(watermark_page)

                # 将合并后的页添加到PDF写入器
                pdf_writer.add_page(input_page)

            # 将结果写入输出PDF文件
            with open(output_pdf, 'wb') as output_file:
                pdf_writer.write(output_file)
        except Exception as e:
            print(e)

    def add_page_footer(self, input_pdf, output_pdf, font_path, font_name, footer_text1, footer_text2):
        """
        给PDF添加页脚
        :param input_pdf:
        :param output_pdf:
        :param font_path:
        :param font_name:
        :param footer_text1:
        :param footer_text2:
        :return:
        """
        pdf_reader = PdfFileReader(input_pdf)
        pdf_writer = PdfFileWriter()
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        for page_number in range(pdf_reader.getNumPages()):
            page = pdf_reader.getPage(page_number)
            page_width, page_height = letter

            # 设置字体大小、行距和水平缩放
            font_size = 9
            line_spacing = 1.20
            horizontal_scale = 110 / 100.0

            def create_footer_canvas(footer_text):
                packet = BytesIO()
                c = canvas.Canvas(packet, pagesize=letter)
                c.setFont(font_name, font_size)
                c.scale(horizontal_scale, 1)
                text_width = c.stringWidth(footer_text, font_name, font_size)
                return c, text_width, packet

            # 添加第一个页脚
            c1, text_width1, packet1 = create_footer_canvas(footer_text1)
            x_position1 = (page_width / 4) - (text_width1 * horizontal_scale) / 2 + 84
            y_position = 10
            c1.drawString(x_position1, y_position, footer_text1)
            c1.save()

            # 添加第二个页脚
            c2, text_width2, packet2 = create_footer_canvas(footer_text2)
            x_position2 = (2.3 * page_width / 4) - (text_width2 * horizontal_scale) / 2 + 30
            c2.drawString(x_position2, y_position, footer_text2)
            c2.save()

            # 将页脚画布移至PDF页面上
            packet1.seek(0)
            footer_canvas1 = PdfFileReader(packet1)
            footer_page1 = footer_canvas1.getPage(0)
            page.mergePage(footer_page1)

            packet2.seek(0)
            footer_canvas2 = PdfFileReader(packet2)
            footer_page2 = footer_canvas2.getPage(0)
            page.mergePage(footer_page2)

            # 将带页脚的页面添加到输出PDF
            pdf_writer.addPage(page)

        # 将修改后的PDF写入文件
        with open(output_pdf, 'wb') as f:
            pdf_writer.write(f)



# 制作表格
import os
import unicodedata
import re


class Generate_Table():
    def __init__(self):
        self.temp_txt_dir = "临时表格"
        self.absolute_path = os.path.dirname(os.getcwd())
        self.generate_file_dir = self.absolute_path + r"\成品"
        if not os.path.exists(self.generate_file_dir):  # 检查目录是否存在
            os.makedirs(self.generate_file_dir)  # 创建目录
        self.filedir = self.absolute_path + r"\生成表格.txt"
        self.cell_width = 16
        # 正则匹配中文字符
        self.pattern = r'[\u4e00-\u9fff，、。：、~《》！？（）{}【】“”‘’]'

    def get_char_width(self, char):
        return 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1

    def get_text_width(self, text):
        return sum(self.get_char_width(char) for char in text)

    def wrap_text(self, text):
        current_list = ''
        final_list = []
        length = 0
        for character in text:
            if re.search(self.pattern, character):
                length += 2
            else:
                length += 1
            current_list += character

            if length == 17 or length == 18:
                final_list.append(current_list)
                current_list = ''
                length = 0
        # 如果最后的current_list不为空，那么也应该添加到final_list中
        if current_list:
            final_list.append(current_list)
        return final_list

    def build_table(self, data):
        # Wrap text in each cell
        data = [[self.wrap_text(cell) for cell in row] for row in data]
        # Get max rows in each cell
        rows_per_cell = [[len(cell) for cell in row] for row in data]
        max_rows_per_row = [max(cell) for cell in rows_per_cell]
        # Build table title
        total_width = self.cell_width * len(data[0]) + len(data[0]) + 1
        remaining_space = total_width
        half_space = remaining_space // 2
        table = f"{' ' * half_space}{' ' * (remaining_space - half_space)}\n"
        # Build top border
        # table = f"{title}\n"
        table += '┌' + '┬'.join(['─' * (self.cell_width // 2) for _ in range(len(data[0]))]) + '┐\n'

        # Add rows
        for i, row in enumerate(data):
            for j in range(max_rows_per_row[i]):
                table += '│'
                for cell in row:
                    if j < len(cell):
                        # Center align for header, left align for others
                        # align = '^' if i == 0 else '<'
                        text = cell[j]
                        remaining_space = self.cell_width - 2 - self.get_text_width(text)
                        # Fill the remaining space with spaces
                        space = ' ' * remaining_space
                        # If text is full width, use left align; otherwise, center align

                        chinese_str_len = len(re.findall(self.pattern, text)) * 2
                        english_str_len = len([item for item in text if
                                               item not in re.findall(self.pattern, text)])
                        all_len = chinese_str_len + english_str_len
                        if all_len >= self.cell_width - 1:
                            align = '<'
                        else:
                            align = '^'
                        # Fill the remaining space with spaces
                        if align == '^':  # center alignment
                            half_space = remaining_space // 2
                            table += f" {' ' * half_space}{text}{' ' * (remaining_space - half_space)} │"
                        else:  # left alignment
                            text_str = f"{text}{' ' * remaining_space}│"
                            chinese_str_len = len(re.findall(self.pattern, text_str)) * 2
                            english_str_len = len([item for item in text_str if item not in re.findall(self.pattern, text_str)]) -1
                            # print(text_str, f"={chinese_str_len},{english_str_len},{chinese_str_len+english_str_len}")
                            if chinese_str_len + english_str_len == self.cell_width:
                                text_str = f"{text}{' ' * remaining_space}│"
                                table += text_str
                            # elif chinese_str_len + english_str_len == self.cell_width - 1:
                            #     text_str = f"{text}{' ' * remaining_space} │"
                            #     table += text_str
                            else:
                                text_str = f"{text}{' ' * remaining_space} │"
                                table += text_str
                    else:
                        table += ' ' * self.cell_width + '│'
                table += '\n'

            if i < len(data) - 1:
                # Add middle border
                table += '├' + '┼'.join(['─' * (self.cell_width // 2) for _ in range(len(row))]) + '┤\n'
            else:
                # Add bottom border
                table += '└' + '┴'.join(['─' * (self.cell_width // 2) for _ in range(len(row))]) + '┘\n'
        return table

    def generate_txt_file(self, write_txt):
        with open(rf"{self.generate_file_dir}\{self.temp_txt_dir}.txt", "w", encoding="utf-8") as file:
            file.write(write_txt)

    # def read_txt(self):
    #     a = '''{'numCol': 5, 'cells': [{'pos': [[139, 195, 330, 195, 330, 226, 141, 226]], 'yec': 0, 'xec': 0, 'ysc': 0, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'both', 'cellId': 0, 'layouts': [], 'pageNum': [3]}, {'pos': [[330, 195, 556, 195, 555, 226, 330, 226]], 'yec': 0, 'xec': 1, 'ysc': 0, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 1, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 420, 'y': 198}, {'x': 469, 'y': 198}, {'x': 469, 'y': 224}, {'x': 420, 'y': 224}], 'blocks': [{'pos': [{'x': 420, 'y': 198}, {'x': 466, 'y': 198}, {'x': 466, 'y': 222}, {'x': 420, 'y': 222}], 'styleId': 56, 'text': '正面'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '正面', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'e7acb1936ee8143346cf25cf4649af37'}], 'pageNum': [3]}, {'pos': [[556, 195, 790, 195, 790, 226, 555, 226]], 'yec': 0, 'xec': 2, 'ysc': 0, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 2, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 657, 'y': 199}, {'x': 703, 'y': 199}, {'x': 703, 'y': 225}, {'x': 657, 'y': 225}], 'blocks': [{'pos': [{'x': 657, 'y': 199}, {'x': 701, 'y': 199}, {'x': 701, 'y': 222}, {'x': 657, 'y': 222}], 'styleId': 57, 'text': '中性'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '中性', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'c04ac08e6c327654abf5dad906a7e16a'}], 'pageNum': [3]}, {'pos': [[790, 195, 1034, 195, 1034, 226, 790, 226]], 'yec': 0, 'xec': 3, 'ysc': 0, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 3, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 889, 'y': 199}, {'x': 936, 'y': 199}, {'x': 936, 'y': 224}, {'x': 889, 'y': 224}], 'blocks': [{'pos': [{'x': 888, 'y': 199}, {'x': 935, 'y': 199}, {'x': 935, 'y': 221}, {'x': 888, 'y': 221}], 'styleId': 58, 'text': '负面'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '负面', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '0db44da5332ec65c0614526a0eabf740'}], 'pageNum': [3]}, {'pos': [[1034, 195, 1216, 195, 1216, 226, 1034, 226]], 'yec': 0, 'xec': 4, 'ysc': 0, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 4, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1124, 'y': 199}, {'x': 1172, 'y': 199}, {'x': 1172, 'y': 224}, {'x': 1124, 'y': 224}], 'blocks': [{'pos': [{'x': 1123, 'y': 198}, {'x': 1169, 'y': 198}, {'x': 1169, 'y': 221}, {'x': 1123, 'y': 221}], 'styleId': 59, 'text': '总和'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '总和', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '83535fdd3067b99fe4cb0dff5aa5b6f0'}], 'pageNum': [3]}, {'pos': [[141, 226, 330, 226, 330, 258, 141, 258]], 'yec': 1, 'xec': 0, 'ysc': 1, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 5, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 164, 'y': 230}, {'x': 255, 'y': 230}, {'x': 255, 'y': 257}, {'x': 164, 'y': 257}], 'blocks': [{'pos': [{'x': 164, 'y': 231}, {'x': 254, 'y': 231}, {'x': 254, 'y': 255}, {'x': 164, 'y': 255}], 'styleId': 31, 'text': '执法方面'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '执法方面', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '8791cbf6d9ebe36ef58acbe3abf1c7ef'}], 'pageNum': [3]}, {'pos': [[330, 226, 555, 226, 555, 258, 330, 258]], 'yec': 1, 'xec': 1, 'ysc': 1, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 6, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 433, 'y': 230}, {'x': 469, 'y': 230}, {'x': 469, 'y': 255}, {'x': 433, 'y': 255}], 'blocks': [{'pos': [{'x': 432, 'y': 231}, {'x': 466, 'y': 231}, {'x': 466, 'y': 253}, {'x': 432, 'y': 253}], 'styleId': 56, 'text': '33'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '33', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'a9e18e7b5561d9651e03984b17ba948b'}], 'pageNum': [3]}, {'pos': [[555, 226, 790, 226, 790, 258, 555, 258]], 'yec': 1, 'xec': 2, 'ysc': 1, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 7, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 665, 'y': 231}, {'x': 703, 'y': 231}, {'x': 703, 'y': 254}, {'x': 665, 'y': 254}], 'blocks': [{'pos': [{'x': 665, 'y': 231}, {'x': 703, 'y': 231}, {'x': 703, 'y': 251}, {'x': 665, 'y': 251}], 'styleId': 60, 'text': '6B'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '6B', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'd752aa321cddf8311cc8db35bba083e2'}], 'pageNum': [3]}, {'pos': [[790, 226, 1034, 226, 1034, 258, 790, 258]], 'yec': 1, 'xec': 3, 'ysc': 1, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 8, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 899, 'y': 232}, {'x': 940, 'y': 232}, {'x': 940, 'y': 253}, {'x': 899, 'y': 253}], 'blocks': [{'pos': [{'x': 898, 'y': 231}, {'x': 939, 'y': 231}, {'x': 939, 'y': 250}, {'x': 898, 'y': 250}], 'styleId': 61, 'text': '工1'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '工', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '0a8e7bff09eb9adf5fd1fb6af04e5358'}], 'pageNum': [3]}, {'pos': [[1034, 226, 1216, 226, 1216, 258, 1034, 258]], 'yec': 1, 'xec': 4, 'ysc': 1, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 9, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1130, 'y': 230}, {'x': 1176, 'y': 231}, {'x': 1176, 'y': 255}, {'x': 1130, 'y': 255}], 'blocks': [{'pos': [{'x': 1129, 'y': 230}, {'x': 1173, 'y': 230}, {'x': 1173, 'y': 252}, {'x': 1129, 'y': 252}], 'styleId': 62, 'text': '22'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '22', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '124e14b81720524e022844bc81fd3a58'}], 'pageNum': [3]}, {'pos': [[141, 258, 330, 258, 330, 289, 141, 289]], 'yec': 2, 'xec': 0, 'ysc': 2, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 10, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 165, 'y': 262}, {'x': 255, 'y': 262}, {'x': 255, 'y': 289}, {'x': 165, 'y': 289}], 'blocks': [{'pos': [{'x': 164, 'y': 262}, {'x': 255, 'y': 262}, {'x': 255, 'y': 287}, {'x': 164, 'y': 287}], 'styleId': 29, 'text': '队伍形象'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '队伍形象', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'c1878579f5c41d0e7be82f2fc1a0c89c'}], 'pageNum': [3]}, {'pos': [[330, 258, 555, 258, 555, 289, 330, 289]], 'yec': 2, 'xec': 1, 'ysc': 2, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 11, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 433, 'y': 261}, {'x': 468, 'y': 261}, {'x': 468, 'y': 287}, {'x': 433, 'y': 287}], 'blocks': [{'pos': [{'x': 433, 'y': 262}, {'x': 468, 'y': 262}, {'x': 468, 'y': 284}, {'x': 433, 'y': 284}], 'styleId': 63, 'text': '1'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '1', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '250d54d3e9ca0160da377e1a3e17b538'}], 'pageNum': [3]}, {'pos': [[555, 258, 790, 258, 790, 289, 555, 289]], 'yec': 2, 'xec': 2, 'ysc': 2, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 12, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 668, 'y': 263}, {'x': 703, 'y': 263}, {'x': 703, 'y': 284}, {'x': 668, 'y': 284}], 'blocks': [{'pos': [{'x': 667, 'y': 263}, {'x': 704, 'y': 263}, {'x': 704, 'y': 281}, {'x': 667, 'y': 281}], 'styleId': 61, 'text': '卫'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '卫', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '8d8736212cbe5cbff82f89e55b202889'}], 'pageNum': [3]}, {'pos': [[790, 258, 1034, 258, 1034, 289, 790, 289]], 'yec': 2, 'xec': 3, 'ysc': 2, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 13, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 899, 'y': 263}, {'x': 936, 'y': 263}, {'x': 936, 'y': 284}, {'x': 899, 'y': 284}], 'blocks': [{'pos': [{'x': 899, 'y': 264}, {'x': 933, 'y': 264}, {'x': 933, 'y': 282}, {'x': 899, 'y': 282}], 'styleId': 64, 'text': '82'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '82', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'ee21bcbf8b5cc76bdbb0fa3f78b3f693'}], 'pageNum': [3]}, {'pos': [[1034, 258, 1216, 258, 1216, 289, 1034, 289]], 'yec': 2, 'xec': 4, 'ysc': 2, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 14, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1131, 'y': 263}, {'x': 1175, 'y': 263}, {'x': 1175, 'y': 284}, {'x': 1131, 'y': 284}], 'blocks': [{'pos': [{'x': 1130, 'y': 263}, {'x': 1174, 'y': 263}, {'x': 1174, 'y': 282}, {'x': 1130, 'y': 282}], 'styleId': 65, 'text': '104'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '104', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': '1a7b3342288bea419c3420f4877308f4'}], 'pageNum': [3]}, {'pos': [[141, 289, 330, 289, 330, 321, 141, 321]], 'yec': 3, 'xec': 0, 'ysc': 3, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 15, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 193, 'y': 294}, {'x': 231, 'y': 294}, {'x': 231, 'y': 319}, {'x': 193, 'y': 319}], 'blocks': [{'pos': [{'x': 192, 'y': 295}, {'x': 231, 'y': 295}, {'x': 231, 'y': 317}, {'x': 192, 'y': 317}], 'styleId': 46, 'text': '上访'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '上访', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '9abc62985f2414a5c107a83ebbffef08'}], 'pageNum': [3]}, {'pos': [[330, 289, 555, 289, 555, 321, 330, 321]], 'yec': 3, 'xec': 1, 'ysc': 3, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'both', 'cellId': 16, 'layouts': [], 'pageNum': [3]}, {'pos': [[555, 289, 790, 289, 790, 321, 555, 321]], 'yec': 3, 'xec': 2, 'ysc': 3, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 17, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 672, 'y': 295}, {'x': 698, 'y': 295}, {'x': 698, 'y': 317}, {'x': 672, 'y': 317}], 'blocks': [{'pos': [{'x': 672, 'y': 296}, {'x': 700, 'y': 296}, {'x': 700, 'y': 315}, {'x': 672, 'y': 315}], 'styleId': 66, 'text': '2'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '2', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '88ef1b6b1ae12c33590946eb43146aca'}], 'pageNum': [3]}, {'pos': [[790, 289, 1034, 289, 1034, 321, 790, 321]], 'yec': 3, 'xec': 3, 'ysc': 3, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 18, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 900, 'y': 295}, {'x': 935, 'y': 295}, {'x': 935, 'y': 317}, {'x': 900, 'y': 317}], 'blocks': [{'pos': [{'x': 900, 'y': 296}, {'x': 936, 'y': 296}, {'x': 936, 'y': 314}, {'x': 900, 'y': 314}], 'styleId': 61, 'text': '卫'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '卫', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'f2267c344fad7ec99a907a9e8685cbdb'}], 'pageNum': [3]}, {'pos': [[1034, 289, 1216, 289, 1216, 321, 1034, 321]], 'yec': 3, 'xec': 4, 'ysc': 3, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 19, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1137, 'y': 295}, {'x': 1172, 'y': 295}, {'x': 1172, 'y': 316}, {'x': 1137, 'y': 316}], 'blocks': [{'pos': [{'x': 1136, 'y': 296}, {'x': 1172, 'y': 296}, {'x': 1172, 'y': 314}, {'x': 1136, 'y': 314}], 'styleId': 67, 'text': '1'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '1', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': '415d50ea2befcafdfd6e8fd224c37104'}], 'pageNum': [3]}, {'pos': [[141, 321, 330, 321, 330, 352, 141, 352]], 'yec': 4, 'xec': 0, 'ysc': 4, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 20, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 164, 'y': 326}, {'x': 254, 'y': 326}, {'x': 254, 'y': 352}, {'x': 164, 'y': 352}], 'blocks': [{'pos': [{'x': 164, 'y': 326}, {'x': 255, 'y': 326}, {'x': 255, 'y': 349}, {'x': 164, 'y': 349}], 'styleId': 68, 'text': '征地拆迁'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '征地拆迁', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'a97155de5d670c5b46baa6b7e04129e8'}], 'pageNum': [3]}, {'pos': [[330, 321, 555, 321, 555, 352, 330, 352]], 'yec': 4, 'xec': 1, 'ysc': 4, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'both', 'cellId': 21, 'layouts': [], 'pageNum': [3]}, {'pos': [[555, 321, 790, 321, 790, 352, 555, 352]], 'yec': 4, 'xec': 2, 'ysc': 4, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 22, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 672, 'y': 327}, {'x': 696, 'y': 327}, {'x': 696, 'y': 349}, {'x': 672, 'y': 349}], 'blocks': [{'pos': [{'x': 672, 'y': 328}, {'x': 697, 'y': 328}, {'x': 697, 'y': 346}, {'x': 672, 'y': 346}], 'styleId': 61, 'text': '1'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '1', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': '954a2558abd0823b308e22d6d7702986'}], 'pageNum': [3]}, {'pos': [[790, 321, 1034, 321, 1034, 352, 790, 352]], 'yec': 4, 'xec': 3, 'ysc': 4, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 23, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 900, 'y': 327}, {'x': 936, 'y': 327}, {'x': 936, 'y': 349}, {'x': 900, 'y': 349}], 'blocks': [{'pos': [{'x': 899, 'y': 328}, {'x': 933, 'y': 328}, {'x': 933, 'y': 346}, {'x': 899, 'y': 346}], 'styleId': 67, 'text': '36'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '36', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '9ce8678105a24d87d1b4ad71c9ff64d9'}], 'pageNum': [3]}, {'pos': [[1034, 321, 1216, 321, 1216, 352, 1034, 352]], 'yec': 4, 'xec': 4, 'ysc': 4, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 24, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1135, 'y': 327}, {'x': 1170, 'y': 327}, {'x': 1170, 'y': 348}, {'x': 1135, 'y': 348}], 'blocks': [{'pos': [{'x': 1134, 'y': 327}, {'x': 1170, 'y': 327}, {'x': 1170, 'y': 345}, {'x': 1134, 'y': 345}], 'styleId': 69, 'text': '37'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '37', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': '2c7d5b6b7530c3e92ea81958d7d25268'}], 'pageNum': [3]}, {'pos': [[141, 352, 330, 352, 330, 385, 139, 385]], 'yec': 5, 'xec': 0, 'ysc': 5, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'left', 'cellId': 25, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 154, 'y': 359}, {'x': 262, 'y': 359}, {'x': 262, 'y': 384}, {'x': 154, 'y': 384}], 'blocks': [{'pos': [{'x': 153, 'y': 359}, {'x': 258, 'y': 359}, {'x': 258, 'y': 382}, {'x': 153, 'y': 382}], 'styleId': 39, 'text': '群体性事件'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '群体性事件', 'alignment': 'left', 'type': 'text', 'pageNum': [3], 'uniqueId': '441d2cfdeb8a1b50b847ce5b06bce333'}], 'pageNum': [3]}, {'pos': [[330, 352, 555, 352, 555, 385, 330, 385]], 'yec': 5, 'xec': 1, 'ysc': 5, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'both', 'cellId': 26, 'layouts': [], 'pageNum': [3]}, {'pos': [[555, 352, 790, 352, 790, 385, 555, 385]], 'yec': 5, 'xec': 2, 'ysc': 5, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'both', 'cellId': 27, 'layouts': [], 'pageNum': [3]}, {'pos': [[790, 352, 1034, 352, 1034, 385, 790, 385]], 'yec': 5, 'xec': 3, 'ysc': 5, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 28, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 904, 'y': 360}, {'x': 933, 'y': 360}, {'x': 933, 'y': 381}, {'x': 904, 'y': 381}], 'blocks': [{'pos': [{'x': 904, 'y': 360}, {'x': 934, 'y': 360}, {'x': 934, 'y': 378}, {'x': 904, 'y': 378}], 'styleId': 64, 'text': '4'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '4', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'd09a095c0cd274ea3dcbc602c18b1eaf'}], 'pageNum': [3]}, {'pos': [[1034, 352, 1216, 352, 1216, 385, 1034, 385]], 'yec': 5, 'xec': 4, 'ysc': 5, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 29, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1138, 'y': 360}, {'x': 1168, 'y': 360}, {'x': 1168, 'y': 381}, {'x': 1138, 'y': 381}], 'blocks': [{'pos': [{'x': 1138, 'y': 361}, {'x': 1168, 'y': 361}, {'x': 1168, 'y': 379}, {'x': 1138, 'y': 379}], 'styleId': 70, 'text': '4'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '4', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': '1a8a849b8f78fc6be7fc09f3c0b2f2c8'}], 'pageNum': [3]}, {'pos': [[139, 385, 330, 385, 330, 420, 139, 420]], 'yec': 6, 'xec': 0, 'ysc': 6, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 30, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 165, 'y': 391}, {'x': 254, 'y': 391}, {'x': 254, 'y': 416}, {'x': 165, 'y': 416}], 'blocks': [{'pos': [{'x': 164, 'y': 390}, {'x': 252, 'y': 390}, {'x': 252, 'y': 414}, {'x': 164, 'y': 414}], 'styleId': 71, 'text': '社会热点'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '社会热点', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '8148eaea59f5e28fcb958902febcb823'}], 'pageNum': [3]}, {'pos': [[330, 385, 555, 385, 555, 420, 330, 420]], 'yec': 6, 'xec': 1, 'ysc': 6, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 31, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 437, 'y': 392}, {'x': 463, 'y': 392}, {'x': 463, 'y': 413}, {'x': 437, 'y': 413}], 'blocks': [{'pos': [{'x': 437, 'y': 392}, {'x': 464, 'y': 392}, {'x': 464, 'y': 410}, {'x': 437, 'y': 410}], 'styleId': 72, 'text': '1'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '1', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '9b6a5018dcb7e76ae271aa95d603b59e'}], 'pageNum': [3]}, {'pos': [[555, 385, 790, 385, 790, 420, 555, 420]], 'yec': 6, 'xec': 2, 'ysc': 6, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 32, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 666, 'y': 392}, {'x': 700, 'y': 392}, {'x': 700, 'y': 413}, {'x': 666, 'y': 413}], 'blocks': [{'pos': [{'x': 665, 'y': 392}, {'x': 699, 'y': 392}, {'x': 699, 'y': 410}, {'x': 665, 'y': 410}], 'styleId': 69, 'text': '37'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '37', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'e749d4a54167037ccf7a31d2be6697ff'}], 'pageNum': [3]}, {'pos': [[790, 385, 1034, 385, 1034, 420, 790, 420]], 'yec': 6, 'xec': 3, 'ysc': 6, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 33, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 900, 'y': 392}, {'x': 935, 'y': 392}, {'x': 935, 'y': 413}, {'x': 900, 'y': 413}], 'blocks': [{'pos': [{'x': 899, 'y': 392}, {'x': 933, 'y': 392}, {'x': 933, 'y': 410}, {'x': 899, 'y': 410}], 'styleId': 5, 'text': '38'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '38', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': '737c8487c56a0ff1b8d330f1b62285dc'}], 'pageNum': [3]}, {'pos': [[1034, 385, 1216, 385, 1216, 420, 1034, 420]], 'yec': 6, 'xec': 4, 'ysc': 6, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 34, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1137, 'y': 392}, {'x': 1172, 'y': 392}, {'x': 1172, 'y': 413}, {'x': 1137, 'y': 413}], 'blocks': [{'pos': [{'x': 1136, 'y': 392}, {'x': 1170, 'y': 392}, {'x': 1170, 'y': 410}, {'x': 1136, 'y': 410}], 'styleId': 5, 'text': '76'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '76', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': 'f9aa74168a6e996c4520f30409364175'}], 'pageNum': [3]}, {'pos': [[139, 420, 330, 420, 330, 451, 141, 451]], 'yec': 7, 'xec': 0, 'ysc': 7, 'xsc': 0, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 35, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 186, 'y': 423}, {'x': 231, 'y': 423}, {'x': 231, 'y': 448}, {'x': 186, 'y': 448}], 'blocks': [{'pos': [{'x': 186, 'y': 422}, {'x': 231, 'y': 422}, {'x': 231, 'y': 446}, {'x': 186, 'y': 446}], 'styleId': 73, 'text': '总和'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '总和', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'aae142f5af5d2bb8c29f7ea0bc7e66af'}], 'pageNum': [3]}, {'pos': [[330, 420, 555, 420, 555, 451, 330, 451]], 'yec': 7, 'xec': 1, 'ysc': 7, 'xsc': 1, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 36, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 430, 'y': 423}, {'x': 467, 'y': 424}, {'x': 467, 'y': 444}, {'x': 430, 'y': 444}], 'blocks': [{'pos': [{'x': 430, 'y': 423}, {'x': 464, 'y': 423}, {'x': 464, 'y': 442}, {'x': 430, 'y': 442}], 'styleId': 5, 'text': '45'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '45', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'ba6c9c7deb0b4ce4812ae8ea4ac4d2bc'}], 'pageNum': [3]}, {'pos': [[555, 420, 790, 420, 790, 451, 555, 451]], 'yec': 7, 'xec': 2, 'ysc': 7, 'xsc': 2, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 37, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 661, 'y': 423}, {'x': 707, 'y': 423}, {'x': 707, 'y': 444}, {'x': 661, 'y': 444}], 'blocks': [{'pos': [{'x': 661, 'y': 423}, {'x': 705, 'y': 423}, {'x': 705, 'y': 441}, {'x': 661, 'y': 441}], 'styleId': 74, 'text': '119'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '119', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'f05f0d09c2ef13ab38009410af29c12b'}], 'pageNum': [3]}, {'pos': [[790, 420, 1034, 420, 1034, 451, 790, 451]], 'yec': 7, 'xec': 3, 'ysc': 7, 'xsc': 3, 'cellUniqueId': None, 'type': 'text', 'alignment': 'center', 'cellId': 38, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 897, 'y': 423}, {'x': 942, 'y': 423}, {'x': 942, 'y': 444}, {'x': 897, 'y': 444}], 'blocks': [{'pos': [{'x': 897, 'y': 423}, {'x': 941, 'y': 423}, {'x': 941, 'y': 442}, {'x': 897, 'y': 442}], 'styleId': 72, 'text': '3P'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '3P', 'alignment': 'center', 'type': 'text', 'pageNum': [3], 'uniqueId': 'a1c1a288d13f1d719d4d8476e95fa95a'}], 'pageNum': [3]}, {'pos': [[1034, 420, 1216, 420, 1216, 453, 1034, 451]], 'yec': 7, 'xec': 4, 'ysc': 7, 'xsc': 4, 'cellUniqueId': None, 'type': 'text', 'alignment': 'right', 'cellId': 39, 'layouts': [{'firstLinesChars': None, 'pos': [{'x': 1130, 'y': 424}, {'x': 1175, 'y': 424}, {'x': 1175, 'y': 445}, {'x': 1130, 'y': 445}], 'blocks': [{'pos': [{'x': 1130, 'y': 424}, {'x': 1172, 'y': 424}, {'x': 1172, 'y': 442}, {'x': 1130, 'y': 442}], 'styleId': 61, 'text': '506'}], 'index': 0, 'subType': None, 'lineHeight': None, 'text': '506', 'alignment': 'right', 'type': 'text', 'pageNum': [3], 'uniqueId': '81fba1303b6ac8082bf76ef1664a95ed'}], 'pageNum': [3]}], 'pos': [{'x': 133, 'y': 179}, {'x': 1224, 'y': 187}, {'x': 1221, 'y': 465}, {'x': 131, 'y': 457}], 'index': 2, 'subType': 'none', 'text': '', 'alignment': 'center', 'type': 'table', 'numRow': 8, 'pageNum': [3], 'uniqueId': 'ffe3c5e964538f2bbab564009b68af30'}'''
    #     print(a)
    #     # with open(filename, 'r', encoding='utf-8') as f:
    #     #     return f.read()

    def Table_main(self, str):
        result_dict = {}
        temp_list = []
        for i in str["cells"]:
            temp_dict = {}
            if len(i["layouts"]) == 0:
                value = ""
            else:
                value = i["layouts"][0]["text"]
            temp_dict[i["yec"]] = value
            temp_list.append(temp_dict)
        for item in temp_list:
            # 由于每个元素都是一个只有一个键值对的字典，我们可以直接获取键和值
            for key, value in item.items():
                # 检查键是否已经在结果字典中
                if key in result_dict:
                    # 如果在，我们就添加这个值到对应的值列表中
                    result_dict[key].append(value)
                else:
                    # 如果不在，我们就创建一个新的键和值列表
                    result_dict[key] = [value]
        # print(result_dict)


        data = [v for _, v in result_dict.items()]
        txt_text = self.build_table(data=data)
        return txt_text
        # self.generate_txt_file(write_txt=txt_text)
        # print(f"表格制作完成，目录：{self.generate_file_dir}\{self.temp_txt_dir}.txt")
        # except Exception as e:
        #     print(f"表格制作出错，错误信息：\n{e}")


