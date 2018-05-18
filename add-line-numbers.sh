#!/bin/bash

BASE=`basename $1 .pdf`
echo "Converting pages to images ($BASE) ..."
gs -dBATCH -dNOPAUSE -sDEVICE=png16m -r96 -sOutputFile="$BASE-%03d.png" "$BASE.pdf"
# convert $BASE.pdf -crop 100x100% png:$BASE
# echo "Ok"

let pg=0
TEX_CMD_TEMPLATE="\\addlinenumbers{%PGNUM}{0}{50}{0}{50}"
TEX_CMD=""
PG=0
for f in $BASE-*.png; do
    if echo $f | grep -q -- "-[0-9][0-9]*\.png$"; then
        out="$BASE-$PG.txt"
        let PG=PG+1
        echo -n "Processing page $PG ..."
        convert $f -flatten -resize 1X1000! -black-threshold 99% -white-threshold 10% -negate -morphology Erode Diamond -morphology Thinning:-1 Skeleton -black-threshold 50% txt:-| sed -e '1d' -e '/#000000/d' -e 's/^[^,]*,//' -e 's/[(]//g' -e 's/:.*//' -e 's/,/ /g' > "$out";
        ADD=`echo $TEX_CMD_TEMPLATE | sed -e"s/%PGNUM/$PG/g"`
        TEX_CMD="$TEX_CMD $ADD"
        rm $f
        echo "Ok"
    fi;
done

cat > $BASE-line-numbers.tex <<EOF
\documentclass[10pt,a4paper]{article}
\usepackage[margin=0cm]{geometry}
\usepackage{tikz}
\usepackage{pgfplotstable}

\newif\ifprintrawlinenumbers
\pgfkeys{print raw line numbers/.is if=printrawlinenumbers,
  print raw line numbers=true}
\newcommand{\addlinenumbers}[5]{
  \pgfmathtruncatemacro{\leftnumber}{(#1-1)}
  \pgfmathtruncatemacro{\rightnumber}{(#1-1)}
  \pgfplotstableread{\pdfname-\leftnumber.txt}\leftlines
  \pgfplotstableread{\pdfname-\rightnumber.txt}\rightlines
  \begin{tikzpicture}[font=\tiny,anchor=east]
  \node[anchor=south west,inner sep=0] (image) at (0,0) {\includegraphics[width=21cm,page=#1]{\pdfname.pdf}};
    \begin{scope}[x={(image.south east)},y={(image.north west)}]
      \pgfplotstableforeachcolumnelement{[index] 0}\of\leftlines\as\position{
        \ifprintrawlinenumbers
          \node [font=\tiny,red] at (0.04,1-\position/1000)         {\pgfplotstablerow};
        \fi
        \pgfmathtruncatemacro{\checkexcluded}{
          (\pgfplotstablerow>=#2 && \pgfplotstablerow<=#3) ? 1 : 0)
        }
        \ifnum\checkexcluded=1
          \pgfmathtruncatemacro\linenumber{\pgfplotstablerow-#2+1}
          \node [font=\tiny,align=right,anchor=east] at (0.08,1-\position/1000) {\linenumber};
        \fi
      }
      \pgfplotstablegetrowsof{\leftlines}
      %\pgfmathtruncatemacro\rightstart{min((\pgfplotsretval-#2),(#3-#2+1))}
      \pgfplotstableforeachcolumnelement{[index] 0}\of\rightlines\as\position{
        \ifprintrawlinenumbers
          \node [font=\tiny,red,anchor=east] at (1.0,1-\position/1000) {\pgfplotstablerow};
        \fi
        \pgfmathtruncatemacro{\checkexcluded}{
                  (\pgfplotstablerow>=#4 && \pgfplotstablerow<=#5) ? 1 : 0)
        }
        \ifnum\checkexcluded=1
          \pgfmathtruncatemacro\linenumber{\pgfplotstablerow-#4+1}
          \node [font=\tiny] at (0.90,1-\position/1000) {\linenumber};
        \fi
      }
    \end{scope}
  \end{tikzpicture}
}

\begin{document}

\def\pdfname{$BASE}
\pgfkeys{print raw line numbers=false}
$TEX_CMD
\end{document}
EOF
xelatex -interaction=nonstopmode $BASE-line-numbers.tex
rm $BASE-*.txt
rm $BASE-line-numbers.aux $BASE-line-numbers.log
