using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Serialization;


namespace TranslationApp
{

	[XmlRoot(ElementName = "Entry")]
	public class Entry
	{
		[XmlElement(ElementName = "Id")]
		public String Id { get; set; }
		[XmlElement(ElementName = "VoiceId")]
		public string VoiceId { get; set; }
		[XmlElement(ElementName = "JapaneseText")]
		public string JapaneseText { get; set; }
		[XmlElement(ElementName = "EnglishText")]
		public string EnglishText { get; set; }
		[XmlElement(ElementName = "Notes")]
		public string Notes { get; set; }
	}

	[XmlRoot(ElementName = "Struct")]
	public class Struct
	{
		[XmlElement(ElementName = "PointerOffset")]
		public string PointerOffset { get; set; }
		[XmlElement(ElementName = "PointerUnknownValue")]
		public string PointerUnknownValue { get; set; }
		[XmlElement(ElementName = "Unknown1Text")]
		public string Unknown1Text{ get; set; }
		[XmlElement(ElementName = "Unknown2Text")]
		public string Unknown2Text { get; set; }
		[XmlElement(ElementName = "PersonJapaneseText")]
		public string PersonJapaneseText { get; set; }
		[XmlElement(ElementName = "PersonEnglishText")]
		public string PersonEnglishText { get; set; }
		[XmlElement(ElementName = "Type")]
		public string Type { get; set; }
		[XmlElement(ElementName = "Entry")]
		public List<Entry> Entries { get; set; }

	}

	[XmlRoot(ElementName = "Static")]
	public class Static
	{
		[XmlElement(ElementName = "PointerOffset")]
		public string PointerOffset { get; set; }
		[XmlElement(ElementName = "JapaneseText")]
		public string JapaneseText { get; set; }
		[XmlElement(ElementName = "EnglishText")]
		public string EnglishText { get; set; }
		[XmlElement(ElementName = "Notes")]
		public string Notes { get; set; }
	}

	[XmlRoot(ElementName = "FileStruct")]
	public class FileStruct
	{
		[XmlElement(ElementName = "Type")]
		public string Type { get; set; }
		[XmlElement(ElementName = "Struct")]
		public List<Struct> Struct { get; set; }
		[XmlElement(ElementName = "Static")]
		public List<Static> Static { get; set; }
	}

	public class EntryElement
    {
		public EntryElement(string PointerOffset, string Id, string JapaneseText, string EnglishText, string PersonJapanese, string PersonEnglish)
        {
			this.PointerOffset = PointerOffset;
			this.Id = Id;
			this.JapaneseText = JapaneseText;
			this.EnglishText = EnglishText;
			this.PersonJapanese = PersonJapanese;
			this.PersonEnglish = PersonEnglish;

        }
		public EntryElement() { }
		public string PointerOffset { get; set; }
		public string Id { get; set; }
		public string JapaneseText { get; set; }
		public string EnglishText { get; set; }
		public string PersonJapanese { get; set; }
		public string PersonEnglish { get; set; }

		public string DisplayText
        {
			
			get { return $"{PersonJapanese}    {JapaneseText.Replace("\n","")}";  }
        }
		
    }






}
