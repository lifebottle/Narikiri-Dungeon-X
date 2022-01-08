
namespace TranslationApp
{
    partial class fMain
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.menuStripMain = new System.Windows.Forms.MenuStrip();
            this.fileToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.storyAndSkitsToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.eventsAndNPCToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.battleTextToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.menuToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.aboutToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.tbPersonJapanese = new System.Windows.Forms.TextBox();
            this.tbPersonEnglish = new System.Windows.Forms.TextBox();
            this.tbJapaneseText = new System.Windows.Forms.TextBox();
            this.tbEnglishText = new System.Windows.Forms.TextBox();
            this.tbNoteText = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.label5 = new System.Windows.Forms.Label();
            this.tcType = new System.Windows.Forms.TabControl();
            this.tabType1 = new System.Windows.Forms.TabPage();
            this.lbEntries = new System.Windows.Forms.ListBox();
            this.label6 = new System.Windows.Forms.Label();
            this.lFile = new System.Windows.Forms.Label();
            this.menuStripMain.SuspendLayout();
            this.tcType.SuspendLayout();
            this.tabType1.SuspendLayout();
            this.SuspendLayout();
            // 
            // menuStripMain
            // 
            this.menuStripMain.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.fileToolStripMenuItem,
            this.aboutToolStripMenuItem});
            this.menuStripMain.Location = new System.Drawing.Point(0, 0);
            this.menuStripMain.Name = "menuStripMain";
            this.menuStripMain.Size = new System.Drawing.Size(1074, 24);
            this.menuStripMain.TabIndex = 0;
            this.menuStripMain.Text = "menuStrip1";
            // 
            // fileToolStripMenuItem
            // 
            this.fileToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.storyAndSkitsToolStripMenuItem,
            this.eventsAndNPCToolStripMenuItem,
            this.battleTextToolStripMenuItem,
            this.menuToolStripMenuItem});
            this.fileToolStripMenuItem.Name = "fileToolStripMenuItem";
            this.fileToolStripMenuItem.Size = new System.Drawing.Size(37, 20);
            this.fileToolStripMenuItem.Text = "File";
            // 
            // storyAndSkitsToolStripMenuItem
            // 
            this.storyAndSkitsToolStripMenuItem.Name = "storyAndSkitsToolStripMenuItem";
            this.storyAndSkitsToolStripMenuItem.Size = new System.Drawing.Size(158, 22);
            this.storyAndSkitsToolStripMenuItem.Text = "Story and Skits";
            this.storyAndSkitsToolStripMenuItem.Click += new System.EventHandler(this.storyAndSkitsToolStripMenuItem_Click);
            // 
            // eventsAndNPCToolStripMenuItem
            // 
            this.eventsAndNPCToolStripMenuItem.Name = "eventsAndNPCToolStripMenuItem";
            this.eventsAndNPCToolStripMenuItem.Size = new System.Drawing.Size(158, 22);
            this.eventsAndNPCToolStripMenuItem.Text = "Events and NPC";
            // 
            // battleTextToolStripMenuItem
            // 
            this.battleTextToolStripMenuItem.Name = "battleTextToolStripMenuItem";
            this.battleTextToolStripMenuItem.Size = new System.Drawing.Size(158, 22);
            this.battleTextToolStripMenuItem.Text = "Battle Text";
            // 
            // menuToolStripMenuItem
            // 
            this.menuToolStripMenuItem.Name = "menuToolStripMenuItem";
            this.menuToolStripMenuItem.Size = new System.Drawing.Size(158, 22);
            this.menuToolStripMenuItem.Text = "Menu";
            // 
            // aboutToolStripMenuItem
            // 
            this.aboutToolStripMenuItem.Name = "aboutToolStripMenuItem";
            this.aboutToolStripMenuItem.Size = new System.Drawing.Size(52, 20);
            this.aboutToolStripMenuItem.Text = "About";
            // 
            // tbPersonJapanese
            // 
            this.tbPersonJapanese.Location = new System.Drawing.Point(402, 116);
            this.tbPersonJapanese.Name = "tbPersonJapanese";
            this.tbPersonJapanese.Size = new System.Drawing.Size(115, 20);
            this.tbPersonJapanese.TabIndex = 3;
            // 
            // tbPersonEnglish
            // 
            this.tbPersonEnglish.Location = new System.Drawing.Point(576, 116);
            this.tbPersonEnglish.Name = "tbPersonEnglish";
            this.tbPersonEnglish.Size = new System.Drawing.Size(115, 20);
            this.tbPersonEnglish.TabIndex = 4;
            // 
            // tbJapaneseText
            // 
            this.tbJapaneseText.Location = new System.Drawing.Point(402, 177);
            this.tbJapaneseText.Multiline = true;
            this.tbJapaneseText.Name = "tbJapaneseText";
            this.tbJapaneseText.Size = new System.Drawing.Size(289, 111);
            this.tbJapaneseText.TabIndex = 5;
            // 
            // tbEnglishText
            // 
            this.tbEnglishText.Location = new System.Drawing.Point(402, 316);
            this.tbEnglishText.Multiline = true;
            this.tbEnglishText.Name = "tbEnglishText";
            this.tbEnglishText.Size = new System.Drawing.Size(289, 111);
            this.tbEnglishText.TabIndex = 6;
            // 
            // tbNoteText
            // 
            this.tbNoteText.Location = new System.Drawing.Point(402, 451);
            this.tbNoteText.Multiline = true;
            this.tbNoteText.Name = "tbNoteText";
            this.tbNoteText.Size = new System.Drawing.Size(289, 39);
            this.tbNoteText.TabIndex = 7;
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(399, 100);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(89, 13);
            this.label1.TabIndex = 8;
            this.label1.Text = "Person Japanese";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(399, 161);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(53, 13);
            this.label2.TabIndex = 9;
            this.label2.Text = "Japanese";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(399, 300);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(41, 13);
            this.label3.TabIndex = 10;
            this.label3.Text = "English";
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(399, 435);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(35, 13);
            this.label4.TabIndex = 11;
            this.label4.Text = "Notes";
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(573, 100);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(77, 13);
            this.label5.TabIndex = 12;
            this.label5.Text = "Person English";
            // 
            // tcType
            // 
            this.tcType.Controls.Add(this.tabType1);
            this.tcType.Location = new System.Drawing.Point(12, 78);
            this.tcType.Name = "tcType";
            this.tcType.SelectedIndex = 0;
            this.tcType.Size = new System.Drawing.Size(295, 412);
            this.tcType.TabIndex = 13;
            // 
            // tabType1
            // 
            this.tabType1.Controls.Add(this.lbEntries);
            this.tabType1.Location = new System.Drawing.Point(4, 22);
            this.tabType1.Name = "tabType1";
            this.tabType1.Padding = new System.Windows.Forms.Padding(3);
            this.tabType1.Size = new System.Drawing.Size(287, 386);
            this.tabType1.TabIndex = 0;
            this.tabType1.UseVisualStyleBackColor = true;
            // 
            // lbEntries
            // 
            this.lbEntries.DrawMode = System.Windows.Forms.DrawMode.OwnerDrawFixed;
            this.lbEntries.FormattingEnabled = true;
            this.lbEntries.Location = new System.Drawing.Point(6, 6);
            this.lbEntries.Name = "lbEntries";
            this.lbEntries.Size = new System.Drawing.Size(275, 368);
            this.lbEntries.TabIndex = 0;
            this.lbEntries.DrawItem += new System.Windows.Forms.DrawItemEventHandler(this.lbEntries_DrawItem);
            this.lbEntries.SelectedIndexChanged += new System.EventHandler(this.lbEntries_SelectedIndexChanged);
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(399, 52);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(35, 13);
            this.label6.TabIndex = 14;
            this.label6.Text = "label6";
            // 
            // lFile
            // 
            this.lFile.AutoSize = true;
            this.lFile.Font = new System.Drawing.Font("Microsoft Sans Serif", 9.75F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lFile.Location = new System.Drawing.Point(13, 52);
            this.lFile.Name = "lFile";
            this.lFile.Size = new System.Drawing.Size(0, 16);
            this.lFile.TabIndex = 15;
            // 
            // fMain
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1074, 541);
            this.Controls.Add(this.lFile);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.tcType);
            this.Controls.Add(this.label5);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.tbNoteText);
            this.Controls.Add(this.tbEnglishText);
            this.Controls.Add(this.tbJapaneseText);
            this.Controls.Add(this.tbPersonEnglish);
            this.Controls.Add(this.tbPersonJapanese);
            this.Controls.Add(this.menuStripMain);
            this.MainMenuStrip = this.menuStripMain;
            this.Name = "fMain";
            this.Text = "Translation App";
            this.menuStripMain.ResumeLayout(false);
            this.menuStripMain.PerformLayout();
            this.tcType.ResumeLayout(false);
            this.tabType1.ResumeLayout(false);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.MenuStrip menuStripMain;
        private System.Windows.Forms.ToolStripMenuItem fileToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem storyAndSkitsToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem eventsAndNPCToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem battleTextToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem menuToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem aboutToolStripMenuItem;
        private System.Windows.Forms.TextBox tbPersonJapanese;
        private System.Windows.Forms.TextBox tbPersonEnglish;
        private System.Windows.Forms.TextBox tbJapaneseText;
        private System.Windows.Forms.TextBox tbEnglishText;
        private System.Windows.Forms.TextBox tbNoteText;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.TabControl tcType;
        private System.Windows.Forms.TabPage tabType1;
        private System.Windows.Forms.Label label6;
        private System.Windows.Forms.Label lFile;
        private System.Windows.Forms.ListBox lbEntries;
    }
}

