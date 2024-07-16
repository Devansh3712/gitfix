function gf() {
	command mkdir -p $HOME/.gitfix
	log_file="$HOME/.gitfix/git.log"
	echo "git $@" > "$log_file"
	command git "$@" 2>&1 | tee -a "$log_file"
}
export -f gf
