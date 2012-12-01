Supybot-UrbanDictionary
=======================

Purpose

    Supybot plugin for UrbanDictionary (http://www.urbandictionary.com)
    
    This plugin uses their hidden? JSON api. Most other plugins and interfaces
    wind up scraping the broken SOAP interface, scrape the mobile/iPhone site,
    instead of using the cleaner API.

Instructions

    Should work fine in python 2.6+. Does not use any non-standard modules
    
    - Optional: add an alias to the main command:
    
        /msg bot Alias add ud urbandictionary
        /msg bot Alias add urban urbandictionary

Commands

    urbandictionary [--options] <term>
