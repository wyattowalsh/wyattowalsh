# docsify-material-icons

[Material Icons](https://material.io/resources/icons/?style=baseline) plugin for [Docsify](https://docsify.js.org).

## Install

1. Insert Material Icons **CSS** into docsify document (index.html)

```html
<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Two+Tone|Material+Icons+Round|Material+Icons+Sharp" rel="stylesheet"/>
```

2. Then insert script plugin into same document

```html
<script src="//unpkg.com/docsify-material-icons/dist/docsify-material-icons.min.js"></script>
```

## Usage

Any text inside of `:` character is processed as CSS style and converted to HTML code for [Material Icons](https://material.io/resources/icons/?style=baseline), example:

```markup
:mi-two-tone check_circle green:
```

This code is converted to :

```html
<i class="material-icons-two-tone">check_circle</i>
```

## Example

1. Run `npm run build`
1. Run `npm run example`
1. Go to [http://localhost:3000/]()

## License

[Apache License](LICENSE)

## TODO

- Better parser to escape code sections
