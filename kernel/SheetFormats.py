__author__ = "Manuel Escriche <mev@tid.es>"


class SpreadsheetFormats:
    def __init__(self, wb):
        self.chapter_title = wb.add_format({'bold': True, 'font_size': 30, 'bg_color': '#002D67', 'font_color':'#FFE616'})
        self.section_title = wb.add_format({'bold': True, 'font_size': 25, 'bg_color': '#60C1CF', 'font_color':'#002D67'})
        self.section_heading = wb.add_format({'font_size': 13, 'italic':True})
        self.section = wb.add_format({'bold':True, 'font_size':12, 'bg_color':'#99CC00', 'text_wrap': True})
        self.bigSection = wb.add_format({'bold':True, 'font_size':20, 'bg_color':'#99CC00', 'text_wrap': True})
        self.link = wb.add_format({'color': 'blue', 'underline': 1, 'align': 'center'})
        self.lefty_link = wb.add_format({'color': 'blue', 'underline': 1, 'align': 'left'})
        self.top_link = wb.add_format({'color': 'blue', 'underline': 1, 'align':'center', 'valign':'top', 'text_wrap': True})
        self.bold = wb.add_format({'bold': True, 'font_size': 12})
        self.bold_right = wb.add_format({'bold': True, 'font_size': 12, 'align':'right'})
        self.red_bold_right = wb.add_format({'font_color':'red', 'bold': True, 'font_size': 12, 'align':'right'})
        self.bold_left = wb.add_format({'bold': True, 'font_size': 12, 'align':'left'})
        self.green = wb.add_format({'font_color':'green'})
        self.bold_green = wb.add_format({'bold': True,'font_color':'green'})
        self.right_bold_green = wb.add_format({'font_color':'green', 'bold': True, 'font_size': 12, 'align':'right'})
        self.red = wb.add_format({'font_color':'red'})
        self.darkred = wb.add_format({'font_color':'cd5c5c'}) #indian red
        self.pending = wb.add_format({'font_color':'#339966'})
        self.blue = wb.add_format({'font_color':'blue'})
        self.blue_bold_right = wb.add_format({'font_color':'blue', 'bold': True, 'font_size': 12, 'align':'right'})
        self.bold_red = wb.add_format({'bold': True, 'font_size': 12, 'font_color':'red'})
        self.column_heading = wb.add_format({'bg_color':'#C0C0C0'})
        self.right_column_heading = wb.add_format({'bg_color':'#C0C0C0','align':'right'})
        self.column_heading_top = wb.add_format({'bg_color':'#C0C0C0','align':'top', 'text_wrap': True})
        self.bold_column_heading_top = wb.add_format({'bold': True, 'bg_color':'#C0C0C0','align':'top', 'text_wrap': True})
        self.top = wb.add_format({'align':'top', 'text_wrap': True})
        self.onlyTop = wb.add_format({'align':'top'})
        self.topRight = wb.add_format({'align':'right', 'valign':'top'})
        self.center = wb.add_format({'align':'center'})
        self.right = wb.add_format({'align':'right'})
        self.action = wb.add_format({'font_color':'#298A08'})
        self.magenta = wb.add_format({'font_color':'magenta'})
        self.brown = wb.add_format({'font_color': 'brown'})
        self.date = wb.add_format({'num_format': 'dd/mm/yyyy'})


if __name__ == "__main__":
    pass