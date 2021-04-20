# Narikiri Dungeon X
An attempt to create a patch for Narikiri Dungeon X (PSP).

## Hacker Notes
Here is one interesting snip, might be useful for Narikiri Dungeon X...  
If you want to know the file names of the data you extract, check this:

![hash](https://raw.githubusercontent.com/pnvnd/Narikiri-Dungeon-X/main/hash.png)  

```
unsigned int hash(const char* string)
{
    unsigned int hash = 0;
    while(*string)
        hash = ((hash << 7) + hash) + (hash << 3) + *string++;
    return hash;
}
```

The files packed inside the `.bin` each have one its filenames...
...Except that they don't appear enywhere in the `.bin`, or any other file in the game.  

Some system files do have their names in the ELF.
Those numbers are not random, they are the hash of the filename string, as per the above function.

## Links
- https://talesofnaridanx.weebly.com/downloads.html
- http://www.mediafire.com/file/g83m35bh2ju746s/top_patch_v012.rar/file

## Credits
- Thanks to Sky for donating resources to get started