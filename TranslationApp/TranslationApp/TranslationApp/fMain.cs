using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Security;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Xml.Serialization;

namespace TranslationApp
{
    public partial class fMain : Form
    {
        public List<EntryElement> entryElements = new List<EntryElement>();
        public EntryElement entryElement = new EntryElement();
        public FileStruct fileStruct;
        public fMain()
        {
            InitializeComponent();
        }

        private void storyAndSkitsToolStripMenuItem_Click(object sender, EventArgs e)
        {
            
            OpenFileDialog fileDialog = new OpenFileDialog();
            fileStruct = new FileStruct();
            if (fileDialog.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    var sr = new StreamReader(fileDialog.FileName);
                    lFile.Text = fileDialog.FileName;

                    XmlSerializer serializer = new XmlSerializer(typeof(FileStruct));
                    using (FileStream stream = File.OpenRead(fileDialog.FileName))
                    {
                        fileStruct = (FileStruct)serializer.Deserialize(stream);
                        lbEntries.DisplayMember = "DisplayText";

                        entryElements = Tools.getEntryElements(fileStruct);
                        lbEntries.DataSource = entryElements;

                        tabType1.Text = "Struct";

                    }
                }
                catch (SecurityException ex)
                {
                    MessageBox.Show($"Security error.\n\nError message: {ex.Message}\n\n" +
                    $"Details:\n\n{ex.StackTrace}");
                }
            }
        }

        private void lbEntries_DrawItem(object sender, DrawItemEventArgs e)
        {
            bool isSelected = ((e.State & DrawItemState.Selected) == DrawItemState.Selected);

            if (e.Index > -1)
            {
                /* If the item is selected set the background color to SystemColors.Highlight 
                 or else set the color to either WhiteSmoke or White depending if the item index is even or odd */
                Color color = isSelected ? SystemColors.Highlight :
                    e.Index % 2 == 0 ? Color.WhiteSmoke : Color.White;

                // Background item brush
                SolidBrush backgroundBrush = new SolidBrush(color);
                // Text color brush
                SolidBrush textBrush = new SolidBrush(e.ForeColor);

                // Draw the background
                e.Graphics.FillRectangle(backgroundBrush, e.Bounds);
                // Draw the text
                e.Graphics.DrawString(lbEntries.GetItemText(lbEntries.Items[e.Index]), e.Font, textBrush, e.Bounds, StringFormat.GenericDefault);


                // Clean up
                backgroundBrush.Dispose();
                textBrush.Dispose();
            }
            e.DrawFocusRectangle();

        }

        private void lbEntries_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (entryElements.Count > 0)
            {
                entryElement = entryElements[lbEntries.SelectedIndex];
                if (tcType.SelectedTab.Text == "Struct")
                {
                    loadStructData();
                }
            }
            
        }

        private void loadStructData()
        {

            Struct myStruct = fileStruct.Struct.Where(x => x.PointerOffset == entryElement.PointerOffset).FirstOrDefault();
            Entry myEntry = myStruct.Entries.Where(x => x.Id == entryElement.Id).FirstOrDefault();

            tbPersonEnglish.Text = myStruct.PersonEnglishText;
            tbPersonJapanese.Text = myStruct.PersonJapaneseText;  

            tbJapaneseText.Text = myEntry.JapaneseText.Replace("\n", Environment.NewLine);
            tbEnglishText.Text = myEntry.EnglishText.Replace("\n", Environment.NewLine);
            tbNoteText.Text = myEntry.Notes;



        }

        private void bSave_Click(object sender, EventArgs e)
        {
            
        }
    }
}

    
