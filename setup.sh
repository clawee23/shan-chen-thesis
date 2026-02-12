#!/bin/bash

# (PREREQUISITE) Install Quarto
# Visit https://quarto.org/docs/get-started/ to install Quarto

# (PREREQUISITE) Install R
# Visit https://cran.r-project.org/ to install R

# Install necessary R libraries
echo "Installing necessary R libraries..."
R --quiet -e "install.packages(c('knitr', 'rmarkdown', 'bookdown'), repos='https://cran.rstudio.com/')"

echo "Setup complete!"
