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

For example, it's actually pretty trivial to "detach" this game, from Phantasia X, resulting in 2 independent ISO's.
> It's just another self inside the game?

Then alpha-out the Phantasia X logo from the menu...and voila!
The game's engine simply reloads the menu if you still try to access it.

## Links
- https://talesofnaridanx.weebly.com/downloads.html
- https://www.youtube.com/user/Crevox/videos
- http://www.mediafire.com/file/g83m35bh2ju746s/top_patch_v012.rar/file

## Credits
- Thanks to `Sky` for donating resources to get started
- Thanks to `crevox` for permission to use their menu patch
- Thanks to `kevassa` for permission to use their English translation script
