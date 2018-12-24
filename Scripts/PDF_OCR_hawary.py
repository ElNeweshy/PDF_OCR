# -*- coding: utf-8 -*-
from pdf2image import convert_from_path
import subprocess
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
import io
import re
import pandas as pd
import os
import numpy as np
import shutil
import string
states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID',
          'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
          'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
          'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'MV',
          'WI', 'WY']
def check_if_all_numbers(line):
    try:
        if re.findall('\d*\.', line)[0] == line:
            return False
    except:
        pass
    return True
def addres_cleaner(group):
    group = [line.replace('\n','') for line in group]
    remove_items = list()
    def remove_characters(line):
        for ch in line:
            if ch in string.ascii_uppercase:
                line = line[line.index(ch):]
                for item in remove_items:
                    group.remove(item)
                return line
        return False

    for line in group:
        if len(line)<6:
            remove_items.append(line)
            continue
        Line = remove_characters(line)
        if Line:
            try:
                group.remove(line)
            except:pass
            group.insert(0,Line)
            for item in remove_items:
                try:
                    group.remove(item)
                except:pass

            group  = [line for line in group if 'EXHIBIT' not in line and check_if_all_numbers(line) ]

            return group
def anyexists(states, line):
    for st in states:
        if st in line:
            if ' '+st+' ' in line:
                return True
    return False



class PDF:
    def __init__(self, PDF_file_name):
        self.PDF_file_name = PDF_file_name
        self.file_name, extension = PDF_file_name.replace(' ', '_').replace('-', '_').split('.')
        self.number_of_pages = len(convert_from_path(self.PDF_file_name, 300))
        self.temp_folder_name = self.file_name.replace(' ', '_')

    @staticmethod
    def create_temp_folder(folder_name):
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
            # os.system("rm -rf {}".format(folder_name))
        os.makedirs(folder_name)

    # Convert PDF to images
    def PDF_to_images(self):
        self.create_temp_folder(self.temp_folder_name)

        pages = convert_from_path(self.PDF_file_name)

        for i, page in enumerate(pages):
            page.save('{}//{}_{}.jpg'.format(self.temp_folder_name, self.file_name, i), 'JPEG')

    # Convert images to separate PDFs after doing the OCR
    def image_to_textPDF(self):
        for item in os.listdir(self.temp_folder_name):
            image_name, extension = item.split('.')
            image_name = image_name.replace(' ', '_')

            subprocess.call(
                'OCRmyPDF {}//{} --image-dpi 96 {}//{}.pdf'.format(self.temp_folder_name, item, self.temp_folder_name,
                                                                   image_name), shell=True)

    # Read the text from PDF after OCR process
    def textPDF_to_text(self):

        for i in range(self.number_of_pages):
            fp = open('{}//{}_{}.pdf'.format(self.temp_folder_name, self.file_name, i), 'rb',encoding='utf-8')

            rsrcmgr = PDFResourceManager()
            retstr = io.StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
            # Create a PDF interpreter object.
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            # Process each page contained in the document.

            for page in PDFPage.get_pages(fp):
                interpreter.process_page(page)
                text = retstr.getvalue()

            textfile = open('{}//{}_{}.txt'.format(self.temp_folder_name, self.file_name, i), 'w',encoding='utf-8')
            textfile.write(text)
            textfile.close()

    def images_to_text(self):
        # This uses tesseract
        for item in os.listdir(self.temp_folder_name):
            image_name, extension = item.split('.')
            image_name = image_name.replace(' ', '_')

            subprocess.call(
                'tesseract {}//{} {}//{}'.format(self.temp_folder_name, item, self.temp_folder_name,
                                                 image_name), shell=True)


class TextFile:
    def __init__(self, file_name):
        self.file_name = file_name

    def read_lines(self):
        txt = open(self.file_name, 'r',encoding='utf-8').readlines()
        return txt

    def raw_file_corrector(self, lines):

        # Remove '=' from lines
        for i, line in enumerate(lines):
            if '=' in line:
                lines[i] = lines[i].replace('=', '')

        # # to remove the lines before the state (1 or 2)
        for i, line in enumerate(lines):
            matcher = re.findall("\n[A-Z][A-Z]\n", line)
            if len(matcher) > 0 and lines[i - 1] == '\n':
                if lines[i - 1] == '\n' and lines[i - 2] == '\n':
                    del lines[i - 1]
                    del lines[i - 1]
                else:
                    del lines[i - 1]


                    # To remove the line between zipcode and state
                    # for i, line in enumerate(lines):
            matcher = re.findall("\n\n[\d]+", line)
            if len(matcher) > 0 and lines[i - 1] == '\n' and lines[i - 2] == '\n' and lines[i - 3][-2:] in states:
                del lines[i - 1]
                lines[i - 2] = lines[i - 2].replace('\n', ' ')

        # To remove the empty line between the last line in the group that includes the city and the above
        # for i, line in enumerate(lines):
        #     matcher = re.findall(",\s\w\w\s\d\d\d\d\d", line)
        #     if len(matcher) > 0 and lines[i - 1] == '\n':
        #         del lines[i - 1]

        # To remove the empty line between the company name and the rest of the group
        # for i, line in enumerate(lines):
        #     matcher = re.findall(",\s\w\w\s\d\d\d\d\d", line)
        #     if len(matcher) > 0 and lines[i - 2] == '\n':
        #         del lines[i - 2]




        # Print lines

        return lines

    def get_text_groups(self, lines, number_of_lines, line_max_length):
        new_line_indices = [i for i, e in enumerate(lines) if  anyexists(states,lines[i])]

        if not new_line_indices: return new_line_indices
        starting = new_line_indices[0]
        while True:
            try:
                starting-=2
                if lines[starting][0]  in '0123456789':
                    new_line_indices.insert(0,starting)
                    break
            except:break
        groups = []
        for i in range(len(new_line_indices)-1):
            if i ==0:
                group = lines[new_line_indices[i]:new_line_indices[i+1]+1]
                if '\n' in group: group=list(filter(lambda item: item != '\n', group))
                groups.append(addres_cleaner(group))
            else:
                group = lines[new_line_indices[i]+1:new_line_indices[i+1]+1]
                if '\n' in group: group=list(filter(lambda item: item != '\n', group))
                groups.append(addres_cleaner(group))
        return groups

    def concatenate_groups(self, groups):
        groups = [' '.join(group) for group in groups]
        return groups

    def get_company_data(self, groups):
        ''' This is customized for specific data set
        e.g.,
        TKG Properties, LLC
        c/o MineralSoft Inc.
        P.O. Box 12787
        Austin, TX 78711
        '''
        states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID',
                  'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
                  'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
                  'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'MV',
                  'WI', 'WY']

        groups_data = []
        for group in groups:
            ResCompanyName = None
            ResFirstName = None
            ResLastName = None
            Address1 = None
            Address2 = None
            City = None
            State = None
            Zipcode = None

            # Checks
            # Check for Zipcode, State, City
            if not group: continue
            for line in group:
                line = line.strip()
                group_check = False
                findings = re.findall(",\s\w\w[.,]?\s\d\d\d\d", line)
                try:
                    State = re.findall("[A-Z][A-Z]", line)
                    State = State[0].strip()
                except:
                    pass

                if len(findings) > 0 and State in states:
                    try:
                        Zipcode = re.findall("\d\d\d\d\d", line)[0]
                    except:
                        Zipcode = re.findall("\d\d\d\d", line)[0]

                    if len(re.findall("\d\d\d\d\d-", line)) > 0:
                        Zipcode = re.findall("\d+-\d+", line)[0]

                    comma_index = line.index(',')
                    City = line[0:comma_index]

                    group_check = True

                    # Remove the empty line
                    group = group[:-1]

            # Check for Address1 and Address2
            for line in group:
                if ('Box' or 'St.') in line:
                    if 'Box' in line:
                        Address1 = line

                    elif 'St.' in line:
                        Address1 = line

                    # remove the line
                    group.remove(line)

                elif 'Suite' in line:
                    comma_index = line.index(',')
                    Address1 = line[:comma_index]
                    Address2 = line[comma_index + 2:]

                    # remove the line
                    group.remove(line)

                elif ('Ste.' or 'STE.') in line:

                    comma_index = line.index(',')
                    Address1 = line[:comma_index]
                    Address2 = line[comma_index + 2:]
                    if ', ' not in line:
                        Address2 = line[comma_index + 1:]

                    # remove the line
                    group.remove(line)

                elif 'P.O' in line:
                    Address1 = line
                    # remove the line
                    group.remove(line)

                else:
                    find_number_in_beggining = re.findall("^[\d+]{2,}", line)
                    if len(find_number_in_beggining) > 0:
                        Address1 = line

                        # remove the line
                        group.remove(line)

            # The remaining is the company name
            ResCompanyName = ' '.join(group)

            if group_check == True:

                group_data = [ResCompanyName, ResFirstName, ResLastName, Address1, Address2, City, State, Zipcode]
                try:
                    group_data = [item[1:] if item != None and item[0] == '-' else item for item in group_data]
                except:
                    pass
                groups_data.append(group_data)

        return groups_data


def create_csv(file_name, list_of_lists=[], columns=None):
    df = pd.DataFrame(list_of_lists, columns=columns)
    df.to_csv(file_name, index=False, encoding='utf-8')


def concatenate_CSVs(folder_name):
    for i, item in enumerate(os.listdir(folder_name)):
        output_file_name = '{}.csv'.format(folder_name)

        if item.split('.')[1] == 'csv':
            if i == 0:
                df = pd.read_csv('{}//{}'.format(folder_name, item))
                create_csv(output_file_name, df,
                           columns=['ResCompanyName', 'ResFirstName', 'ResLastName', 'Address1', 'Address2', 'City',
                                    'State', 'Zipcode'])
            else:
                with open(output_file_name, 'a',encoding='utf-8') as f:
                    df = pd.read_csv('{}//{}'.format(folder_name, item))
                    df.to_csv(f, header=False, index=False)
                    f.close()

    # Add index to the final output
    def add_index(csv_file_name):
        df = pd.read_csv(csv_file_name)
        df.index = np.arange(1, len(df) + 1)
        df.to_csv(csv_file_name, header=True, index=True, index_label='No.')

    add_index(output_file_name)


def get_pdf():
    cwd = os.getcwd()
    PDFs = os.listdir(cwd)

    pdfs = []
    for pdf in PDFs:
        try:
            if pdf.split('.')[1] == 'pdf':
                pdfs.append(pdf)
        except:
            continue

    return (pdfs[0])




if __name__ == '__main__':
    # Process the PDF
    read_pdf_file = get_pdf()
    pdf_file = PDF(read_pdf_file)
    pdf_file.PDF_to_images()
    pdf_file.images_to_text()
    folder_name = pdf_file.temp_folder_name

    ###################################

    # Get info from text file
    for item in os.listdir(folder_name):
        if item.endswith('txt'):
            txt_file = TextFile('{}//{}'.format(folder_name, item))
            lines = txt_file.read_lines()
            # corrected_lines = txt_file.raw_file_corrector(lines)
            lines = [line.replace('=','') if '=' in line else line for line in lines]
            groups = txt_file.get_text_groups(lines, [3, 8], 50)
            data = txt_file.get_company_data(groups)
            final_csv_file_name = '{}//{}.csv'.format(folder_name, item.split('.')[0])
            create_csv(final_csv_file_name, list_of_lists=data,
                       columns=['ResCompanyName', 'ResFirstName', 'ResLastName', 'Address1', 'Address2', 'City',
                                'State', 'Zipcode'])

    #####################################
    # Concatenate CSV
    concatenate_CSVs(folder_name)
    print('The process is done, check: ', '{}.csv'.format(folder_name))
