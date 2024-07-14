function gf() {
	command mkdir -p $HOME/.gitfix
	log_file="$HOME/.gitfix/git.log"
	echo "git $@" > "$log_file"
	command git "$@" 2>&1 | tee "$log_file"

	if [ ${PIPESTATUS[0]} -ne 0 ]; then
		gitfix
	fi
}
export -f gf
