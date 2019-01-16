# -*- coding: utf-8 -*-
import subprocess
import io
import re
import os
import shutil

from pdf2image import convert_from_path
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
import pandas as pd
import numpy as np

states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID',
          'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
          'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
          'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'MV',
          'WI', 'WY']


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
        os.makedirs(folder_name)

    # Convert PDF to images
    def PDF_to_images(self):
        self.create_temp_folder(self.temp_folder_name)

        pages = convert_from_path(self.PDF_file_name)  # Change resolution

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
            fp = open('{}//{}_{}.pdf'.format(self.temp_folder_name, self.file_name, i), 'rb')

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

            textfile = open('{}//{}_{}.txt'.format(self.temp_folder_name, self.file_name, i), 'w')
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
        self.edited_file_name = self.file_name.split('.')[0] + '_new' + '.txt'

    def read_lines(self):
        txt = open(self.edited_file_name, 'r', encoding='utf-8').readlines()
        return txt

    #####################################################################################

    def clean_file(self):

        txt = open(self.file_name, 'r').readlines()
        new_txt = []
        for i, item in enumerate(txt):

            # Remove '='
            if '=' in item:
                item = item.replace('=', '')

            # Remove '\n
            if item.endswith('\n'):
                item = item[:-1]

            # Remove numbers alone in the line
            matcher = re.findall("^\d{1,3}\.", item)
            if len(matcher) > 0:
                item = item[len(matcher[0]) + 1:]

            # Replace 'EXHIBIT' with empty line
            if item.strip() and len(item) > 2:
                matcher1 = re.findall("EXHIBIT", item)
                matcher2 = re.findall("Exhibit", item)
                if len(matcher1) > 0 or len(matcher2):
                    item = ''

                # Replace 'page' with empty line
                matcher = re.findall("PAGE", item)
                if len(matcher) > 0:
                    item = ''

                new_txt.append(item)

        # Add line after the last line in the gorup
        final_txt = []
        for i, item in enumerate(new_txt):

            # concatenate the separated zip code
            matcher = re.findall("[.,]?\s\w\w[.,]?\s{1,2}\d+", item)

            # print('this', item, new_txt)
            if i < len(new_txt) - 2:
                next_matcher = re.findall("^\d+$", new_txt[i + 1])
                if item.endswith('-') and len(next_matcher) > 0:
                    item = item + new_txt[i + 1]
                    new_txt[i + 1] = ''

            # Add separator line
            if len(matcher) > 0:
                final_txt.append(item)
                final_txt.append('')
            else:
                final_txt.append(item)

        # TODO: Remove
        # for item in final_txt:
        #     if item != '':
        #         item = item + "\n"

        # final_final_txt
        # for item in final_txt:
        #     print(item)

        with open(self.edited_file_name, 'w') as output:
            for item in final_txt:
                output.write(item)
                output.write('\n')

        # print(final_txt)
        return final_txt

    #####################################################################################

    def get_text_groups(self, lines, number_of_lines, line_max_length):
        min_number_lines, max_number_lines = number_of_lines
        new_line_indices = [i for i, e in enumerate(lines) if e == '']

        groups = []
        for i in range(len(new_line_indices) - 1):
            if min_number_lines + 1 <= new_line_indices[i + 1] - new_line_indices[i] <= max_number_lines + 1:
                # print(lines)
                group = lines[new_line_indices[i] + 1: new_line_indices[i + 1]]
                # print(group)
                # Remove \n from the end of each line
                # group = [item[:-1] for item in group]

                # Check line length in each group
                lengths_of_lines = [len(line) for line in group]

                if max(lengths_of_lines) <= line_max_length:
                    groups.append(group)

        print('The groups we have are: ', groups)
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
            for line in group:
                line = line.strip()
                group_check = False
                findings = re.findall("[.,]?\s\w\w[.,]?\s{1,2}\d+", line)  # [.,]?\s\w\w[.,]?\s{1,2}\d+   ## ,\s\w\w[.,]?\s\d\d\d\d

                if len(findings) < 1:
                    print('This line is not identifier ', line)

                else:
                    print('The identifier is found: ', findings)

                try:
                    State = re.findall("\s[A-Z]{2}\s", line)
                    State = State[0].strip()
                except:
                    pass

                print('findings: ', findings, 'State:', State)

                if len(findings) > 0 and State in states:       # and State in states
                    print('Here we succeded ________________:', State)

                    try:
                        Zipcode = re.findall("\d\d\d\d\d", line)[0]
                    except:
                        Zipcode = re.findall("\d\d\d\d", line)[0]

                    if len(re.findall("\d+-\d+", line)) > 0:
                        Zipcode = re.findall("\d+-\d+", line)[0]

                    try:
                        comma_index = line.index(',')
                        City = line[0:comma_index]
                    except:
                        comma_index = line.index(State)
                        City = line[0:comma_index]

                    group_check = True

                    # Remove the empty line
                    group = group[:-1]

                    print('Captured Group: ', group)

            # Check for Address1 and Address2
            for line in group:
                if ('Box' or 'St.' or 'BOX') in line:
                    if 'Box' in line:
                        Address1 = line

                    elif 'BOX' in line:
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
                    # if ',' not in line:
                    #     print(line)
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
                # print('here', group_data)
                # group_data = [item[1:] if item != None and item[0] == '-' else item for item in group_data]

                print('Group: ', group)
                print('Group Data: ', group_data)
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
                with open(output_file_name, 'a') as f:
                    df = pd.read_csv('{}//{}'.format(folder_name, item))
                    df.to_csv(f, header=False, index=False)
                    f.close()

    # Add index to the final output
    def add_index(csv_file_name):
        df = pd.read_csv(csv_file_name)
        df.index = np.arange(1, len(df) + 1)
        df.to_csv(csv_file_name, header=True, index=True, index_label='No.')

    add_index(output_file_name)


def get_pdfs():
    cwd = os.getcwd()
    PDFs = os.listdir(cwd)
    pdfs = []

    for pdf in PDFs:
        try:
            if pdf.split('.')[1] == 'pdf':
                pdfs.append(pdf)
        except:
            continue

    if len(pdfs) == 0:
        print('No PDFs in the directory')
        exit()

    return pdfs


if __name__ == '__main__':
    version = '1.2'
    print('PDF_OCR version {} is running ...'.format(version), '\n')

    # # Process the PDF
    read_pdf_files = get_pdfs()

    print('{} PDFs are found'.format(len(read_pdf_files)))
    print(read_pdf_files, '\n')

    for read_pdf_file in read_pdf_files:
        print('Initializing {}'.format(read_pdf_file), '\n')
        pdf_file = PDF(read_pdf_file)
        pdf_file.PDF_to_images()
        pdf_file.images_to_text()
        folder_name = pdf_file.temp_folder_name


        ###################################

        # Get info from text file
        for item in os.listdir(folder_name):
            if item.endswith('txt'):
                txt_file = TextFile('{}//{}'.format(folder_name, item))
                # lines = txt_file.read_lines()

                # corrected_lines = txt_file.raw_file_corrector(lines)

                corrected_file = txt_file.clean_file()

                groups = txt_file.get_text_groups(corrected_file, [2, 8], 50)
                data = txt_file.get_company_data(groups)
                final_csv_file_name = '{}//{}.csv'.format(folder_name, item.split('.')[0])
                create_csv(final_csv_file_name, list_of_lists=data,
                           columns=['ResCompanyName', 'ResFirstName', 'ResLastName', 'Address1', 'Address2', 'City',
                                    'State', 'Zipcode'])

        #####################################
        # Concatenate CSV
        concatenate_CSVs(folder_name)
        print('__________________________________________________________')
        print('The process is done, check: ', '{}.csv'.format(folder_name), '\n')

        #####################################
        # Delete the folder after creating the CSV
        # try:
        #     shutil.rmtree(folder_name)
        # except:
        #     continue

    #########################################
    print('__________________________________________________________')
    print('Creating all the CSVs is done.')
