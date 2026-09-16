interface ErrorMessageProps {
  message?: string
}

function ErrorMessage({
  message = 'Something went wrong. Please try again.',
}: ErrorMessageProps) {
  return (
    <div className="flex min-h-40 items-center justify-center">
      <div className="max-w-md rounded-2xl border border-red-400/20 bg-red-400/5 px-6 py-5 text-center">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-red-400/10 text-red-400">
          !
        </div>

        <h3 className="mt-3 text-sm font-semibold text-red-300">
          Unable to load data
        </h3>

        <p className="mt-2 text-xs leading-5 text-slate-400">
          {message}
        </p>
      </div>
    </div>
  )
}

export default ErrorMessage