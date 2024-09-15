# FinleyEx Blog Site

This repository contains code and posts for my blog site, FinleyEx (also [joshfinley.github.io](https://joshfinley.github.io)).

## Contents

This repository contains source and content for [Hugo](https://github.com/gohugoio/hugo) static web content generation for my blog. Docker is used for repeatable deployments and dependency management, and various scripts are included for other tasks.

## Design Principles

This codebase is designed with the following principles in mind:

- Maximal minimalism: Plain text is superior to dynamic content, but we need not avoid tools that improve our ability to generate and maintain text documents.

- Dependency wariness: Dependency (in its various forms) puts a lifetime on digital content. We must be careful to minimize it, but we can never be free from it.

- Fear of the future: All stored data and information has a lifetime, and we should do what we can to extend it, preferably through data duplication.

To this end, custom themes and additional tools can be used to facilitate the creation & management of text documents, control over software versions and perform archiving and reference updating. These design principles 

### Document Management

Maintaining metadata in documents is challenging. This is why static site generators like [Hugo](https://github.com/gohugoio/hugo) and [Hakyll](https://jaspervdj.be/hakyll/) exist. With such tools we can write text documents in a more abstract way, allowing us to pay less attention to tasks like formatting and metadata management. Compilation and templatization enable us to generate output documents that stand on their own right. If the toolchain for generating documents goes away, the documents that had previously been generated will remain.

### Dependency Management

Still, we can employ tools like [Docker](https://en.wikipedia.org/wiki/Docker_(software)) and [Git](https://en.wikipedia.org/wiki/Git) to help fight against the inevitable destruction of our toolchain. Docker might have its own dependency and abstraction issues, but for the near term it will enable a reasonable lifetime for the toolchain.

### Reference Management

Although web monetization has resulted in walled gardens around certain content, data duplication and intelligent referencing can mitigate many of the issues with link rot. Archival sources are useful, but the best way to know you will have access to something is to hold a copy of it yourself.

## Building

To build and run the container, make sure you have Docker installed and run the following commands:

```
sudo docker build -t hugo-image .
sudo docker run --rm -p 1313:1313 -v $(pwd):/site hugo-image server -D --bind 0.0.0.0
```

Additionally, the `debug.sh` script can be used to run the container while making changes, similar to the `--watch` option for Hugo.

## Site Customizations

- [x] Post indexing based on tags & categories
- [x] Date sorting for new posts and Index population
- [x] Automatic table of contents generation
- [x] Automatic heading numbering
- [x] Backlinks generation & propagation
- [x] Bibliography generation
- [ ] Quotes with bibliography population
- [ ] Reference archival and reference rewriting
- [x] Footnote support & footnote organization
- [ ] Fancy blockquote and nested blockquote support
- [ ] Content linting, spellchecking
- [ ] Automatic generation of changelog based on commits
- [ ] Link mapping

## Design Customizations

- [ ] Monochrome aesthetic
- [ ] Vaguely academic layout
- [ ] Hearty use of whitespace (where appropriate)
- [ ] Attractive bullet points
- [ ] Syntax highlighting