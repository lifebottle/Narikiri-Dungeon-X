# Narikiri Dungeon X
An attempt to create a patch for Narikiri Dungeon X (PSP).  
https://docs.google.com/spreadsheets/d/1S1RwcAVeOqBEnIhfU2z7ZVff2C3vqwJ1tvNcy_qHZ6w/edit#gid=0

## Hacker Note 1
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


## Hacker Note 2
1. Besides the executable, `all.dat` is the only file of the game
2. Indices are in the executable, Offset + size + name hash.  So each entry should be 12-bytes, given each member 32-bits
3. Are the "sub-files" padded to start at an LBA? I think so, try searching for both (should take 2 minutes)
4. Just identify the padding in the biggile to know where a subfile starts. Then seach both offsets and sector in the exe. And you'll find the entry table.
5. Now the game doesn't store names anywhere, but rather generates them at runtime. Then hashes the generated names and looks it up in the index table to find offset and size. If you want to extract the right file names, you need to bruteforce the hashes from the index table with the function above (Hacker Note 1)

## Hacker Note 3
The game engine statically links something like `libc`, so it uses `sprintf` to generate in runtime file names.
For instance `sprintf('levels/%d/enemy/%s/model.dat", 7, "bat");`
Just a made up case. Then it would hash `"levels/5/enemy/bat/model.dat"`
So theoretically if you know all the folders you can brute force faster
Some system files, like the font, have fine names directly stored in the execuable
Those are easy to get, just run strings on the exe. Hash all, and take the ones existing in the entry table
There is also the fact that the hash is a partially reversible function
Meaning that a small change in the source string, causes a small change in the resulting hash
With all this... the hashes could be all recovered

## Hacker Note 4
Other aspects of the game are somewhat easy to hack, like the font
It's just a set of `gim` files. You can't find them using the GE debugger though...
Just find the font name in the exe, hash it and get the font from the bigfile with its offset and size
Decode the gim and that's it

## Links
- https://talesofnaridanx.weebly.com/downloads.html
- https://www.youtube.com/user/Crevox/videos
- http://www.mediafire.com/file/g83m35bh2ju746s/top_patch_v012.rar/file

## Credits
- Thanks to `Sky` for donating resources to get started
- Thanks to `crevox` for permission to use their menu patch
- Thanks to `kevassa` for permission to use their English translation script
