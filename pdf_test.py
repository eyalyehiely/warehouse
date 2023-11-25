from fpdf import FPDF

data = [1, 2, 3, 4, 5, 6]

pdf = FPDF(format='letter')
pdf.add_page()
pdf.set_font("Arial", size=12)

for item in data:
    pdf.write(5, str(item))
pdf.output("testings.pdf")
