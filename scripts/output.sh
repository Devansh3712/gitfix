function git() {
	command mkdir -p $HOME/.gitfix
	log_file="$HOME/.gitfix/git.log"
	echo "git $@" > "$log_file"
	command git -c color.ui=always "$@" 2>&1 | tee "$log_file"
}
export -f git
