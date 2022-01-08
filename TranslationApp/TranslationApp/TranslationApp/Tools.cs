using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Serialization;

namespace TranslationApp
{
    public static class Tools
    {
        public static List<EntryElement> getEntryElements(FileStruct storyText)
        {
            List<EntryElement> res = new List<EntryElement>();
            List<Entry> entries = new List<Entry>();
            List<Struct> listStruct = storyText.Struct;
            string pointerOffset = "";

            foreach (Struct ele in listStruct)
            {

                pointerOffset = ele.PointerOffset;
                entries = ele.Entries;
                foreach (Entry entry in entries)
                {
                    res.Add(new EntryElement(pointerOffset, entry.Id, entry.JapaneseText, entry.EnglishText, ele.PersonJapaneseText, ele.PersonEnglishText));
                }
            }
            return res;

        }

    }
}
